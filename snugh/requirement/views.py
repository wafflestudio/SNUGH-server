from rest_framework import status, viewsets
from rest_framework.response import Response
from django.db import transaction
from requirement.models import *
from requirement.serializers import RequirementSerializer
from requirement.utils import calculate_progress, requirement_histroy_generator
from user.models import *
from user.serializers import *
from lecture.models import *
from rest_framework.decorators import action
from django.db.models import Prefetch, Sum


class RequirementViewSet(viewsets.GenericViewSet):
    """
    Generic ViewSet of Requirement Object.
    # TODO: Permission constraint for admin user
    """
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer

    # POST /requirement
    @transaction.atomic
    def create(self, request):
        """
        Create new static requirements. Used for one-time purposes.
        """
        majors = Major.objects.prefetch_related(
            Prefetch(
                'requirement',
                queryset=Requirement.objects.all(),
                to_attr="requirements")).all()
        reqs = []
        req_miss_majors = []
        for major in majors:
            major_type = major.major_type
            requirements = major.requirements
            if major_type in [MAJOR, SINGLE_MAJOR]:
                std = {ALL, GENERAL, MAJOR_ALL, MAJOR_REQUIREMENT}
                std_len = 4
            else:
                std = {MAJOR_ALL, MAJOR_REQUIREMENT}
                std_len = 2
            std -= set([req.requirement_type for req in requirements])
            for type in std:
                reqs.append(
                    Requirement(
                        major=major,
                        requirement_type=type,
                        is_auto_generated=True
                ))
            if len(std) == std_len:
                req_miss_majors.append(major)
        Requirement.objects.bulk_create(reqs)

        body = {"majors": MajorSerializer(req_miss_majors, many=True).data}
        return Response(body, status=status.HTTP_201_CREATED)


    # GET /requirement/:planId/calculate
    @action(methods=['GET'], detail=True)
    def calculate(self, request):
        """Show user plan's current progress based on plan requirements."""
        plan_id = request.query_params.get('plan_id')
        plan = Plan.objects.prefetch_related(
            'planmajor', 
            'planrequirement', 
            'planrequirement__requirement', 
            'planrequirement__requirement__major', 
            'semester'
            ).get(id=plan_id)
        majors = plan.planmajor.all().values('major', 'major__major_name', 'major__major_type')
        majors_info = {}
        for major in majors:
            major_id = major['major']
            major_name = major['major__major_name']
            major_type = major['major__major_type']
            majors_info[major_id] = {
                'major_name':major_name,
                'major_type':major_type
            }

        planrequirements = plan.planrequirement.all()
        all_earned_credit = 0
        all_required_credit = 0
        general_earned_credit = 0
        general_requirement_credit = 0
        major_earned_credit = 0
        major_all_pr_list = {}
        major_requirement_pr_list = {}

        for pr in planrequirements:
            pr.earned_credit = 0
            req = pr.requirement
            if req.requirement_type == ALL:
                if all_required_credit < pr.required_credit:
                    all_required_credit = pr.required_credit
                    all_planrequirement = pr
            elif req.requirement_type == GENERAL:
                if general_requirement_credit < pr.required_credit:
                    general_requirement_credit = pr.required_credit
                    general_planrequirement = pr
            elif req.requirement_type == MAJOR_ALL:
                req_major_id = req.major.id
                if req_major_id in majors_info.keys():
                    major_all_pr_list[req_major_id] = pr
            elif req.requirement_type == MAJOR_REQUIREMENT:
                req_major_id = req.major.id
                if req_major_id in majors_info.keys():
                    major_requirement_pr_list[req_major_id] = pr

        sl_list = plan.semester.all().values(
            'semesterlecture', 
            'semesterlecture__credit', 
            'semesterlecture__lecture_type1',
            'semesterlecture__lecture_type2',
            'semesterlecture__recognized_major1',
            'semesterlecture__recognized_major2')

        for sl in sl_list:
            credit = sl['semesterlecture__credit']
            lecture_type1 = sl['semesterlecture__lecture_type1']
            lecture_type2 = sl['semesterlecture__lecture_type2']
            recognized_major1_id = sl['semesterlecture__recognized_major1']
            recognized_major2_id = sl['semesterlecture__recognized_major2']

            # all
            all_earned_credit+=credit

            # general
            if lecture_type1 == GENERAL:
                general_earned_credit+=credit

            # major_all, major_requirement (주의: 만약 plan의 major가 아닌데 전필/전선으로 되어 있으면 에러뜸)
            elif lecture_type1 in [MAJOR_REQUIREMENT, MAJOR_ELECTIVE]:
                major_earned_credit+=credit
                major_all_pr_list[recognized_major1_id].earned_credit += credit
                if lecture_type1 == MAJOR_REQUIREMENT:
                    major_requirement_pr_list[recognized_major1_id].earned_credit += credit
                if recognized_major2_id != DEFAULT_MAJOR_ID:
                    if lecture_type2 in [MAJOR_REQUIREMENT, MAJOR_ELECTIVE]:
                        major_all_pr_list[recognized_major2_id].earned_credit += credit
                        if lecture_type2 == MAJOR_REQUIREMENT:
                            major_requirement_pr_list[recognized_major2_id].earned_credit += credit

        all_planrequirement.earned_credit = all_earned_credit
        general_planrequirement.earned_credit = general_earned_credit

        major_requirement_progress_required  = 0
        major_requirement_progress_earned = 0

        for pr in major_all_pr_list.values():
            major_requirement_progress_required += pr.required_credit
            major_requirement_progress_earned += pr.earned_credit
        
        all_requirement = {"required_credit": all_required_credit,
                           "earned_credit": all_earned_credit,
                           "progress": calculate_progress(all_required_credit, all_earned_credit)}

        general_requirement = {"earned_credit": general_earned_credit,
                             "progress": calculate_progress(general_requirement_credit, general_earned_credit)}

        major_requirement = {"earned_credit": major_earned_credit,
                               "progress": calculate_progress(major_requirement_progress_required, major_requirement_progress_earned)}

        other_requirement = {"earned_credit": all_earned_credit - general_earned_credit - major_earned_credit}

        all_progress_summary = {"all": all_requirement,
                                "major": major_requirement,
                                "general": general_requirement,
                                "other": other_requirement,
                                "current_planmajors": majors_info.values()
                                }

        # calculate major progress
        major_progress = []
        for major_id in majors_info.keys():
            mr_rc = major_requirement_pr_list[major_id].required_credit
            mr_ec = major_requirement_pr_list[major_id].earned_credit
            major_requirement_required_credit = {"required_credit": mr_rc,
                                                 "earned_credit": mr_ec,
                                                 "progress": calculate_progress(mr_rc, mr_ec)}

            ma_rc = major_all_pr_list[major_id].required_credit
            ma_ec = major_all_pr_list[major_id].earned_credit
            major_all_required_credit = {"required_credit": ma_rc,
                                         "earned_credit": ma_ec,
                                         "progress": calculate_progress(ma_rc, ma_ec)}

            major_progress.append({"major_id": major_id,
                                   "major_name": majors_info[major_id]['major_name'],
                                   "major_type": majors_info[major_id]['major_type'],
                                   "major_requirement_credit": major_requirement_required_credit,
                                   "major_all_credit": major_all_required_credit})

        if plan.is_first_simulation:
            plan.is_first_simulation = False
            plan.save()

        PlanRequirement.objects.bulk_update(planrequirements, fields=['earned_credit'])

        data = {"all_progress": all_progress_summary,
                "major_progress": major_progress}
        return Response(data, status=status.HTTP_200_OK)


    # GET /requirement
    def list(self, request, pk=None):
        """Get user plan's requirements."""
        plan = Plan.objects.prefetch_related(
            'planmajor', 
            'planrequirement', 
            'planrequirement__requirement', 
            'planrequirement__requirement__major', 
            'semester'
            ).get(pk=pk)
        majors = plan.planmajor.all().values('major', 'major__major_name', 'major__major_type')
        majors_info = {}
        for major in majors:
            major_id = major['major']
            major_name = major['major__major_name']
            major_type = major['major__major_type']
            majors_info[major_id] = {
                'major_name':major_name,
                'major_type':major_type
            }
        planrequirements = plan.planrequirement.all()
        is_necessary = False

        all_required_credit = 0
        general_requirement_credit = 0
        for pr in planrequirements:
            req = pr.requirement
            if req.requirement_type == ALL:
                if all_required_credit < pr.required_credit:
                    all_required_credit = pr.required_credit
            elif req.requirement_type == GENERAL:
                if general_requirement_credit < pr.required_credit:
                    general_requirement_credit = pr.required_credit
            elif req.requirement_type in [MAJOR_ALL, MAJOR_REQUIREMENT]:
                req_major_id = req.major.id
                if req.requirement_type == MAJOR_ALL:
                    majors_info[req_major_id]['major_credit'] = pr.required_credit
                else:
                    majors_info[req_major_id]['major_requirement_credit'] = pr.required_credit
                    majors_info[req_major_id]['auto_calculate'] = pr.auto_calculate

        data = {
            "majors": majors_info.values(),
            "all": all_required_credit,
            "general": general_requirement_credit,
            "is_first_simulation": plan.is_first_simulation,
            "is_necessary": is_necessary
        }

        return Response(data, status=status.HTTP_200_OK)


    # PUT /requirement/:planId
    @transaction.atomic
    def update(self, request, pk=None):
        """Update plan requirements required credits."""
        user = request.user
        plan = Plan.objects.prefetch_related(
            "planrequirement",
            "planrequirement__requirement",
            "planrequirement__requirement__major",
            "planrequirement__requirement__major__majorlecture",
            "planrequirement__requirement__major__majorlecture__lecture"

        ).get(pk=pk)
        majors = request.data.get('majors')
        all_credit = request.data.get('all')
        general_credit = request.data.get('general')
        data = {
            "majors": {},
            "all": all_credit,
            "general": general_credit
        }

        planrequirements = plan.planrequirement.all()
        all_std = 0
        gen_std = 0
        year_std = user.userprofile.entrance_year
        histories = []
        pr_list = []
        for pr in planrequirements:
            req = pr.requirement
            if not (req.major.major_name in data['majors'].keys()):
                data['majors']['req.major.major_name'] = {
                    'major_type': req.major.major_type,
                    "major_credit":req.major.required_credit,
                    "major_requirement_credit": req.major.required_credit,
                    "auto_calculate": req.major.auto_calculate

                }
            if req.requirement_type==ALL:
                if all_std < req.required_credit:
                    all_std = req.required_credit
                    all_pr = pr
            elif req.requirement_type==GENERAL:
                if gen_std < req.required_credit:
                    gen_std = req.required_credit
                    gen_pr = pr
            elif req.requirement_type == MAJOR_ALL:
                for major in majors:
                    if req.major.major_name == major['major_name'] and req.major.major_type == major['major_type']:
                        if pr.required_credit != major["major_credit"]: 
                            pr.required_credit = major["major_credit"]
                            histories.append(
                                requirement_histroy_generator(
                                    requirement=req,
                                    entrance_year=year_std,
                                    past_required_credit=pr.required_credit,
                                    curr_required_credit=major["major_credit"]
                                )
                            )
                            pr_list.append(pr)
                            data['majors'][major['major_name']]['major_credit'] = major["major_credit"]
            elif req.requirement_type == MAJOR_REQUIREMENT:
                for major in majors:
                    if req.major.major_name == major['major_name'] and req.major.major_type == major['major_type']:
                        pr.auto_calculate = major['auto_calculate']
                        if pr.auto_calculate:
                            major_requirement_credit = req.major.majorlecture.filter(
                                lecture_type= MAJOR_REQUIREMENT, 
                                start_year__lte=year_std,
                                end_year__gte=year_std).values(
                                    'lecture__credit'
                                ).aggregate(mrc=Sum('lecture__credit'))['mrc']
                        else:
                            major_requirement_credit = major["major_requirement_credit"]
                            
                        if pr.required_credit != major_requirement_credit:
                            pr.required_credit = major_requirement_credit
                            histories.append(
                                requirement_histroy_generator(
                                    requirement=req,
                                    entrance_year=year_std,
                                    past_required_credit=pr.required_credit,
                                    curr_required_credit=major["major_credit"]
                                )
                            )
                            pr_list.append(pr)
                            data['majors'][major['major_name']]['major_requirement_credit'] = major_requirement_credit
                            data['majors'][major['major_name']]['auto_calculate'] = major['auto_calculate']
        if all_pr.required_credit != all_credit:
            all_pr.required_credit = all_credit
            histories.append(
                requirement_histroy_generator(
                    requirement=all_pr.req,
                    entrance_year=year_std,
                    past_required_credit=all_pr.required_credit,
                    curr_required_credit=all_credit
                )
            )
            pr_list.append(all_pr)
        if gen_pr.required_credit != general_credit:
            gen_pr.required_credit = general_credit
            histories.append(
                requirement_histroy_generator(
                    requirement=gen_pr.req,
                    entrance_year=year_std,
                    past_required_credit=gen_pr.required_credit,
                    curr_required_credit=general_credit
                )
            )
            pr_list.append(gen_pr)
        PlanRequirement.objects.bulk_update(pr_list, fields=["required_credit"])
        RequirementChangeHistory.objects.bulk_update(histories, ["change_count"])

        for major_name, value in data['majors'].items():
            value['major_name'] = major_name
        data['majors'] = list(data['majors'].values())

        return Response(data, status=status.HTTP_200_OK)
