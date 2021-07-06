from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from requirement.models import Requirement, PlanRequirement
from requirement.serializers import RequirementSerializer, ProgressSerializer
from user.models import Major
from lecture.models import Plan, PlanMajor, SemesterLecture


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

        # calculate earned credit of plan_requirement
        sl_list = list(SemesterLecture.objects.filter(semester__plan=plan))
        for sl in sl_list:
            r1 = Requirement.objects.get(major=sl.recognized_major1, requirement_type=sl.lecture_type1)
            pr1 = PlanRequirement.objects.get(plan=plan, requirement=r1)
            pr1.earned_credit += sl.lecture.credit
            pr1.save()

            if sl.recognized_major2.id != Major.DEFAULT_MAJOR_ID:
                r2 = Requirement.objects.get(major=sl.recognized_major2, requirement_type=sl.lecture_type2)
                pr2 = PlanRequirement.objects.get(plan=plan, requirement=r2)
                pr2.earned_credit += sl.lecture.credit
                pr2.save()

        # calculate all progress
        major_requirement = {"required_credit": 0,
                             "earned_credit": 0,
                             "progress": 0}

        general_requirement = {"required_credit": 0,
                               "earned_credit": 0,
                               "progress": 0}

        general_elective_requirement = {"required_credit": 0,
                                        "earned_credit": 0,
                                        "progress": 0}

        all_requirement = {"required_credit": 0,
                           "earned_credit": 0,
                           "progress": 0}

        for major in list(majors):
            # major_requirement
            mr_pr = PlanRequirement.objects.get(plan=plan,
                                                requirement__major=major,
                                                requirement__requirement_type=Requirement.MAJOR_REQUIREMENT)
            mr_rc = mr_pr.requirement.required_credit
            mr_ec = mr_pr.earned_credit
            major_requirement["required_credit"] += mr_rc
            major_requirement["earned_credit"] += mr_ec
            all_requirement ["required_credit"] += mr_rc
            all_requirement ["earned_credit"] += mr_ec

            # major_elective
            me_pr = PlanRequirement.objects.get(plan=plan,
                                                requirement__major=major,
                                                requirement__requirement_type=Requirement.MAJOR_ELECTIVE)
            me_rc = me_pr.requirement.required_credit
            me_ec = me_pr.earned_credit
            major_requirement["required_credit"] += me_rc
            major_requirement["earned_credit"] += me_ec
            all_requirement["required_credit"] += me_rc
            all_requirement["earned_credit"] += me_ec

            # teaching
            try:
                t_pr = PlanRequirement.objects.get(plan=plan,
                                                   requirement__major=major,
                                                   requirement__requirement_type=Requirement.TEACHING)
                t_rc = t_pr.requirement.required_credit
                t_ec = t_pr.earned_credit
                major_requirement["required_credit"] += t_rc
                major_requirement["earned_credit"] += t_ec
                all_requirement["required_credit"] += t_rc
                all_requirement["earned_credit"] += t_ec
            except PlanRequirement.DoesNotExist:
                pass

            # general
            try:
                g_pr = PlanRequirement.objects.get(plan=plan,
                                                   requirement__major=major,
                                                   requirement__requirement_type=Requirement.GENERAL)
                g_rc = g_pr.requirement.required_credit
                g_ec = g_pr.earned_credit
                general_requirement["required_credit"] += g_rc
                general_requirement["earned_credit"] += g_ec
                all_requirement["required_credit"] += g_rc
                all_requirement["earned_credit"] += g_ec
            except PlanRequirement.DoesNotExist:
                pass

            # general_elective
            try:
                ge_pr = PlanRequirement.objects.get(plan=plan,
                                                    requirement__major=major,
                                                    requirement__requirement_type=Requirement.GENERAL_ELECTIVE)
                ge_rc = ge_pr.requirement.required_credit
                ge_ec = ge_pr.earned_credit
                general_elective_requirement["required_credit"] += ge_rc
                general_elective_requirement["earned_credit"] += ge_ec
                all_requirement["required_credit"] += ge_rc
                all_requirement["earned_credit"] += ge_ec
            except PlanRequirement.DoesNotExist:
                pass

        major_requirement["progress"] = round(major_requirement["earned_credit"] / major_requirement["required_credit"], 2)
        general_requirement["progress"] = round(general_requirement["earned_credit"] / general_requirement["required_credit"], 2)
        general_elective_requirement["progress"] = 1
        all_requirement["progress"] = round(all_requirement["earned_credit"] / all_requirement["required_credit"], 2)

        all_progress = {"major": major_requirement,
                        "general": general_requirement,
                        "general_elective": general_elective_requirement,
                        "all": all_requirement}

        # calculate major progress
        major_progress = []
        for major in list(majors):
            mr_pr = PlanRequirement.objects.get(plan=plan,
                                                requirement__major=major,
                                                requirement__requirement_type=Requirement.MAJOR_REQUIREMENT)
            mr_rc = mr_pr.requirement.required_credit
            mr_ec = mr_pr.earned_credit
            major_requirement_credit = {"required_credit": mr_rc,
                                        "earned_credit": mr_ec,
                                        "progress": round(mr_ec/mr_rc, 2)}

            me_pr = PlanRequirement.objects.get(plan=plan,
                                                requirement__major=major,
                                                requirement__requirement_type=Requirement.MAJOR_ELECTIVE)
            me_rc = me_pr.requirement.required_credit
            me_ec = me_pr.earned_credit
            major_elective_credit = {"required_credit": me_rc,
                                     "earned_credit": me_ec,
                                     "progress": round(me_ec/me_rc, 2)}

            major_progress.append({"major_id": major.id,
                                   "major_name": major.major_name,
                                   "major_type": major.major_type,
                                   "major_requirement_credit": major_requirement_credit,
                                   "major_elective_credit": major_elective_credit})

        # calculate general progress
        general_progress = general_requirement

        data = {"all_progress": all_progress,
                "major_progress": major_progress,
                "general_progress": general_progress}
        return Response(data, status=status.HTTP_200_OK)

    # PUT /requirement/
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