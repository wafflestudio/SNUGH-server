from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from requirement.models import Requirement, PlanRequirement
from requirement.serializers import RequirementSerializer, ProgressSerializer
from user.models import *
from user.serializers import *
from lecture.models import *
from rest_framework.decorators import action


class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer

    # GET /requirement/
    @transaction.atomic
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.query_params.get('plan_id', None)
        if plan_id is None:
            return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)
        plan = get_object_or_404(Plan, pk=plan_id)
        majors = Major.objects.filter(planmajor__plan=plan)

        # init earned credit of plan_requirement
        pr_list = list(PlanRequirement.objects.filter(plan=plan))
        for pr in pr_list:
            pr.earned_credit = 0
            pr.save()

        # requirement_type = all
        all_requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                     requirement_type=Requirement.ALL).order_by('-required_credit').first()
        all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=all_requirement)
        all_required_credit = all_planrequirement.required_credit
        all_earned_credit = 0

        # requirement_type = general
        general_requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                         requirement_type=Requirement.GENERAL).order_by('-required_credit').first()
        general_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=general_requirement)
        general_requirement_credit = general_planrequirement.required_credit
        general_earned_credit = 0

        major_earned_credit = 0 # 전공교과 총 이수 학점

        # requirement_type = major_all
        major_all_pr_list = {}
        for major in majors:
            major_all_requirement = Requirement.objects.get(planrequirement__plan=plan,
                                                 requirement_type=Requirement.MAJOR_ALL, major=major)
            major_all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=major_all_requirement)
            major_all_pr_list[major] = major_all_planrequirement

        # requirement_type = major_requirement
        major_requirement_pr_list = {}
        for major in majors:
            major_requirement_requirement = Requirement.objects.get(planrequirement__plan=plan,
                                                                    requirement_type=Requirement.MAJOR_REQUIREMENT,
                                                                    major=major)
            major_requirement_planrequirement = PlanRequirement.objects.get(plan=plan,
                                                                            requirement=major_requirement_requirement)
            major_requirement_pr_list[major] = major_requirement_planrequirement

        sl_list = list(SemesterLecture.objects.filter(semester__plan=plan))

        for sl in sl_list:
            credit = sl.lecture.credit
            # all
            all_earned_credit+=credit

            # general
            if sl.lecture_type1 == Lecture.GENERAL:
                general_earned_credit +=credit

            # major_all, major_requirement
            elif sl.lecture_type1 == Lecture.MAJOR_REQUIREMENT or sl.lecture_type1 == Lecture.MAJOR_ELECTIVE:
                major_earned_credit+=credit
                # 주의: 만약 plan의 major가 아닌데 전필/전선으로 되어 있으면 에러뜸
                major_all_pr_list[sl.recognized_major1].earned_credit += credit
                major_all_pr_list[sl.recognized_major1].save()
                if sl.lecture_type1 == Lecture.MAJOR_REQUIREMENT:
                    major_requirement_pr_list[sl.recognized_major1].earned_credit += credit
                    major_requirement_pr_list[sl.recognized_major1].save()

                if sl.recognized_major2.id != Major.DEFAULT_MAJOR_ID:
                    if sl.lecture_type2 == Lecture.MAJOR_REQUIREMENT or sl.lecture_type2 == Lecture.MAJOR_ELECTIVE:
                        major_all_pr_list[sl.recognized_major2].earned_credit += credit
                        major_all_pr_list[sl.recognized_major2].save()
                        if sl.lecture_type2 == Lecture.MAJOR_REQUIREMENT:
                            major_requirement_pr_list[sl.recognized_major2].earned_credit += credit
                            major_requirement_pr_list[sl.recognized_major2].save()

        all_planrequirement.earned_credit = all_earned_credit
        all_planrequirement.save()
        general_planrequirement.earned_credit = general_earned_credit
        general_planrequirement.save()

        # # calculate earned credit of plan_requirement
        # for sl in sl_list:
        #     r1 = Requirement.objects.get(major=sl.recognized_major1, requirement_type=sl.lecture_type1, )
        #     pr1 = PlanRequirement.objects.get(plan=plan, requirement=r1)
        #     pr1.earned_credit += sl.lecture.credit
        #     pr1.save()
        #
        #     if sl.recognized_major2.id != Major.DEFAULT_MAJOR_ID:
        #         r2 = Requirement.objects.get(major=sl.recognized_major2, requirement_type=sl.lecture_type2)
        #         pr2 = PlanRequirement.objects.get(plan=plan, requirement=r2)
        #         pr2.earned_credit += sl.lecture.credit
        #         pr2.save()

        # calculate all progress
        all_requirement = {"required_credit": 0,
                           "earned_credit": 0,
                           "progress": 0}

        major_requirement = {"earned_credit": 0,
                             "progress": 0}

        general_requirement = {"earned_credit": 0,
                               "progress": 0}

        other_requirement = {"earned_credit": 0}

        # for major in list(majors):
        #     # major_requirement
        #     mr_pr = PlanRequirement.objects.get(plan=plan,
        #                                         requirement__major=major,
        #                                         requirement__requirement_type=Requirement.MAJOR_REQUIREMENT)
        #     mr_rc = mr_pr.requirement.required_credit
        #     mr_ec = mr_pr.earned_credit
        #     major_requirement["required_credit"] += mr_rc
        #     major_requirement["earned_credit"] += mr_ec
        #     all_requirement["required_credit"] += mr_rc
        #     all_requirement["earned_credit"] += mr_ec
        #
        #     # major_elective
        #     me_pr = PlanRequirement.objects.get(plan=plan,
        #                                         requirement__major=major,
        #                                         requirement__requirement_type=Requirement.MAJOR_ELECTIVE)
        #     me_rc = me_pr.requirement.required_credit
        #     me_ec = me_pr.earned_credit
        #     major_requirement["required_credit"] += me_rc
        #     major_requirement["earned_credit"] += me_ec
        #     all_requirement["required_credit"] += me_rc
        #     all_requirement["earned_credit"] += me_ec
        #
        #     # teaching
        #     try:
        #         t_pr = PlanRequirement.objects.get(plan=plan,
        #                                            requirement__major=major,
        #                                            requirement__requirement_type=Requirement.TEACHING)
        #         t_rc = t_pr.requirement.required_credit
        #         t_ec = t_pr.earned_credit
        #         major_requirement["required_credit"] += t_rc
        #         major_requirement["earned_credit"] += t_ec
        #         all_requirement["required_credit"] += t_rc
        #         all_requirement["earned_credit"] += t_ec
        #     except PlanRequirement.DoesNotExist:
        #         pass
        #
        #     # general
        #     try:
        #         g_pr = PlanRequirement.objects.get(plan=plan,
        #                                            requirement__major=major,
        #                                            requirement__requirement_type=Requirement.GENERAL)
        #         g_rc = g_pr.requirement.required_credit
        #         g_ec = g_pr.earned_credit
        #         general_requirement["required_credit"] += g_rc
        #         general_requirement["earned_credit"] += g_ec
        #         all_requirement["required_credit"] += g_rc
        #         all_requirement["earned_credit"] += g_ec
        #     except PlanRequirement.DoesNotExist:
        #         pass
        #
        #     # general_elective
        #     try:
        #         ge_pr = PlanRequirement.objects.get(plan=plan,
        #                                             requirement__major=major,
        #                                             requirement__requirement_type=Requirement.GENERAL_ELECTIVE)
        #         ge_rc = ge_pr.requirement.required_credit
        #         ge_ec = ge_pr.earned_credit
        #         general_elective_requirement["required_credit"] += ge_rc
        #         general_elective_requirement["earned_credit"] += ge_ec
        #         all_requirement["required_credit"] += ge_rc
        #         all_requirement["earned_credit"] += ge_ec
        #     except PlanRequirement.DoesNotExist:
        #         pass

        major_requirement_progress_required  = 0
        major_requirement_progress_earned = 0

        for major in major_all_pr_list:
            major_requirement_progress_required += major_all_pr_list[major].required_credit
            major_requirement_progress_earned += major_all_pr_list[major].earned_credit

        all_requirement["required_credit"] = all_required_credit

        all_requirement["earned_credit"] = all_earned_credit
        general_requirement["earned_credit"] = general_earned_credit
        major_requirement["earned_credit"] = major_earned_credit
        other_requirement["earned_credit"] = all_earned_credit - general_earned_credit - major_earned_credit

        major_requirement["progress"] = round(major_requirement_progress_earned / major_requirement_progress_required, 2)
        general_requirement["progress"] = round(general_requirement["earned_credit"] / general_requirement_credit, 2)
        all_requirement["progress"] = round(all_requirement["earned_credit"] / all_requirement["required_credit"], 2)

        all_progress_summary = {"all": all_requirement,
                                "major": major_requirement,
                                "general": general_requirement,
                                "other": other_requirement,
                                "current_planmajors": MajorSerializer(majors, many=True).data # 에러나면 여기
                                }

        # calculate major progress
        major_progress = []
        for major in list(majors):
            mr_rc = major_requirement_pr_list[major].required_credit
            mr_ec = major_requirement_pr_list[major].earned_credit
            major_requirement_required_credit = {"required_credit": mr_rc,
                                                 "earned_credit": mr_ec,
                                                 "progress": round(mr_ec/mr_rc, 2)}

            ma_rc = major_all_pr_list[major].required_credit
            ma_ec = major_all_pr_list[major].earned_credit
            major_all_required_credit = {"required_credit": ma_rc,
                                         "earned_credit": ma_ec,
                                         "progress": round(ma_ec/ma_rc, 2)}

            major_progress.append({"major_id": major.id,
                                   "major_name": major.major_name,
                                   "major_type": major.major_type,
                                   "major_requirement_credit": major_requirement_required_credit,
                                   "major_all_credit": major_all_required_credit})

        # # calculate general progress
        # general_progress = general_requirement

        data = {"all_progress": all_progress_summary,
                "major_progress": major_progress}
        return Response(data, status=status.HTTP_200_OK)

    # GET /requirement/{plan_id}/loading/
    @action(methods=['GET'], detail=True)
    @transaction.atomic
    def loading(self, request, pk=None):
        plan = Plan.objects.get(pk=pk)
        majors = Major.objects.filter(planmajor__plan=plan)

        # 자유전공학부 때문에 filter => 자전 외에는 major가 두개인 경우는 없어야 정상
        all_requirement = Requirement.objects.filter(planrequirement__plan=plan, requirement_type=Requirement.ALL).order_by('-required_credit').first()
        all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=all_requirement)

        general_requirement = Requirement.objects.filter(planrequirement__plan=plan, requirement_type=Requirement.GENERAL).order_by('-required_credit').first()
        general_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=general_requirement)

        major_requirement_list = []

        for major in majors:
            major_all_requirement = Requirement.objects.get(planrequirement__plan=plan, requirement_type=Requirement.MAJOR_ALL, major=major)
            major_all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=major_all_requirement)

            major_requirement_requirement = Requirement.objects.get(planrequirement__plan=plan, requirement_type=Requirement.MAJOR_REQUIREMENT, major=major)
            major_requirement_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=major_requirement_requirement)

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

    # PUT /requirement/{plan_id}/settings/
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
        # 자유전공학부 때문에 filter => 자전 외에는 major가 두개인 경우는 없어야 정상
        all_requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                     requirement_type=Requirement.ALL).order_by('-required_credit').first()
        all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=all_requirement)
        all_planrequirement.required_credit = all_credit
        all_planrequirement.save()

        general_requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                         requirement_type=Requirement.GENERAL).order_by('-required_credit').first()
        general_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=general_requirement)
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
                major_requirement_planrequirement.required_credit = major_requirement_credit
                major_requirement_planrequirement.save()
            else:
                major_requirement_planrequirement.required_credit = major_credit["major_requirement_credit"]
                major_requirement_planrequirement.save()

        # response for debugging
        major_requirement_list = []

        for major in majors:
            major_all_requirement = Requirement.objects.get(planrequirement__plan=plan,
                                                            requirement_type=Requirement.MAJOR_ALL, major=major)
            major_all_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=major_all_requirement)

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

    @transaction.atomic
    def put(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        update_list = request.data.copy()
        for curr_request in update_list:
            plan_id = curr_request['plan_id']
            requirement_id = curr_request['requirement_id']
            is_fulfilled = curr_request['is_fulfilled']

            plan = Plan.objects.get(pk=plan_id)
            requirement = Requirement.objects.get(pk=requirement_id)
            planrequirement = PlanRequirement.objects.filter(plan=plan, requirement=requirement)
            planrequirement.update(is_fulfilled=is_fulfilled)

        return Response(status=status.HTTP_200_OK)
