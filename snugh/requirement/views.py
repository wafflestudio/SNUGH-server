from rest_framework import status, viewsets
from rest_framework.response import Response
from django.db import transaction
from requirement.models import *
from requirement.serializers import RequirementSerializer
from requirement.utils import calculate_progress
from user.models import *
from user.serializers import *
from lecture.models import *
from rest_framework.decorators import action
from django.db.models import Prefetch

class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer
    # TODO: Permission constraint for admin user

    # POST /requirement
    # 1회성 generating api
    @transaction.atomic
    def create(self, request):
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

    # GET /requirement
    def list(self, request):

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

        # TODO: need to check current_planmajors
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

    # GET /requirement/:planId/loading
    @action(methods=['GET'], detail=True)
    def loading(self, request, pk=None):
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

    # PUT /requirement/:planId/setting
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def setting(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = Plan.objects.get(pk=pk)
        majors = Major.objects.filter(planmajor__plan=plan)

        major_credit_list = request.data.get('majors')
        all_credit = request.data.get('all')
        general_credit = request.data.get('general')

        # update all&general planrequirements
        # 자유전공학부 때문에 filter (자전 외에는 major가 두개인 경우는 없어야 정상)
        all_requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                     requirement_type=Requirement.ALL).order_by('-required_credit').first()
        all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=all_requirement)
        if all_planrequirement.required_credit != all_credit:
            # requirementchangehistory
            check_requirement_change_history(all_requirement, all_credit, user.userprofile.entrance_year)
            # update
            all_planrequirement.required_credit = all_credit
            all_planrequirement.save()

        general_requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                         requirement_type=Requirement.GENERAL).order_by('-required_credit').first()
        general_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=general_requirement)
        if general_planrequirement.required_credit != general_credit:
            # requirementchangehistory
            check_requirement_change_history(general_requirement, general_credit, user.userprofile.entrance_year)
            # update
            general_planrequirement.required_credit = general_credit
            general_planrequirement.save()

        # update major planrequirements
        for major_credit in major_credit_list:
            major_name = major_credit["major_name"]
            major_type = major_credit["major_type"]
            major = Major.objects.get(major_name=major_name, major_type=major_type)

            major_all_requirement = Requirement.objects.get(planrequirement__plan=plan,
                                                            requirement_type=Requirement.MAJOR_ALL, major=major)
            major_all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=major_all_requirement)
            if major_all_planrequirement.required_credit != major_credit["major_credit"]:
                check_requirement_change_history(major_all_requirement, major_credit["major_credit"],user.userprofile.entrance_year)
                major_all_planrequirement.required_credit = major_credit["major_credit"]
                major_all_planrequirement.save()

            major_requirement_requirement = Requirement.objects.get(planrequirement__plan=plan,
                                                                    requirement_type=Requirement.MAJOR_REQUIREMENT,
                                                                    major=major)
            major_requirement_planrequirement = PlanRequirement.objects.get(plan=plan,
                                                                            requirement=major_requirement_requirement)
            major_requirement_planrequirement.auto_calculate = major_credit["auto_calculate"]
            if major_credit["auto_calculate"]:
                major_requirement_credit = 0
                mr_lectures = Lecture.objects.filter(majorlecture__major=major, majorlecture__lecture_type= Lecture.MAJOR_REQUIREMENT, majorlecture__start_year__lte=user.userprofile.entrance_year,
                                                    majorlecture__end_year__gte=user.userprofile.entrance_year)
                for mr_lecture in mr_lectures:
                    major_requirement_credit += mr_lecture.credit

                if major_requirement_planrequirement.required_credit != major_requirement_credit:
                    check_requirement_change_history(major_requirement_requirement, major_requirement_credit, user.userprofile.entrance_year)
                    major_requirement_planrequirement.required_credit = major_requirement_credit
                    major_requirement_planrequirement.save()
            else:
                if major_requirement_planrequirement.required_credit != major_credit["major_requirement_credit"]:
                    check_requirement_change_history(major_requirement_requirement, major_credit["major_requirement_credit"], user.userprofile.entrance_year)
                    major_requirement_planrequirement.required_credit = major_credit["major_requirement_credit"]
                    major_requirement_planrequirement.save()

        major_requirement_list = []

        for major in majors:
            major_all_requirement = Requirement.objects.get(planrequirement__plan=plan,
                                                            requirement_type=Requirement.MAJOR_ALL, major=major)
            major_all_planrequirement = PlanRequirement.objects.get(plan=plan,
                                                                    requirement=major_all_requirement)

            major_requirement_requirement = Requirement.objects.get(planrequirement__plan=plan,
                                                                    requirement_type=Requirement.MAJOR_REQUIREMENT,
                                                                    major=major)
            major_requirement_planrequirement = PlanRequirement.objects.get(plan=plan,
                                                                            requirement=major_requirement_requirement)

            data = {
                "major_name": major.major_name,
                "major_type": major.major_type,
                "major_credit": major_all_planrequirement.required_credit,
                "major_requirement_credit": major_requirement_planrequirement.required_credit,
                "auto_calculate": major_requirement_planrequirement.auto_calculate
            }

            major_requirement_list.append(data)

        data = {
            "majors": major_requirement_list,
            "all": all_planrequirement.required_credit,
            "general": general_planrequirement.required_credit
        }

        return Response(data, status=status.HTTP_200_OK)

# Common Functions
def check_requirement_change_history(requirement, changed_credit, entrance_year):
    requirementchangehistory = RequirementChangeHistory.objects.filter(requirement=requirement,
                                                                       entrance_year=entrance_year,
                                                                       past_required_credit=requirement.required_credit,
                                                                       curr_required_credit=changed_credit)
    if requirementchangehistory.count() == 0:
        RequirementChangeHistory.objects.create(requirement=requirement,
                                               entrance_year=entrance_year,
                                               past_required_credit=requirement.required_credit,
                                               curr_required_credit=changed_credit)
    else:
        requirementchangehistory = RequirementChangeHistory.objects.get(requirement=requirement,
                                                                       entrance_year=entrance_year,
                                                                       past_required_credit=requirement.required_credit,
                                                                       curr_required_credit=changed_credit)
        requirementchangehistory.change_count += 1
        requirementchangehistory.save()
