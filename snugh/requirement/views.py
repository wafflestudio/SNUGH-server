from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from requirement.models import Requirement, PlanRequirement
from requirement.serializers import RequirementSerializer, ProgressSerializer
from user.models import Major
from lecture.models import Plan, PlanMajor


class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer

    # GET /requirement/
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.query_params.get('plan_id', None)
        search_type = request.query_params.get('search_type', None)

        if plan_id is None:
            return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)
        if search_type is None:
            return Response({"error": "search_type missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "plan_id not_exist"}, status=status.HTTP_404_NOT_FOUND)

        majors = Major.objects.filter(planmajor__plan=plan)

        result_list = []
        if search_type == "all":
            for major in list(majors):
                plan_requirements = PlanRequirement.objects.filter(plan=plan, requirement__major=major)
                serializer = self.get_serializer(plan_requirements, many=True)
                requirements = serializer.data
                result_list.append({"major_name": major.major_name,
                                    "major_type": major.major_type,
                                    "requirements": requirements})
        elif search_type == "credit":
            for major in list(majors):
                plan_requirements = PlanRequirement.objects.filter(plan=plan, requirement__major=major,
                                                                   requirement__is_credit_requirement=True)
                serializer = self.get_serializer(plan_requirements, many=True)
                requirements = serializer.data
                result_list.append({"major_name": major.major_name,
                                    "major_type": major.major_type,
                                    "requirements": requirements})
        elif search_type == "etc":
            for major in list(majors):
                plan_requirements = PlanRequirement.objects.filter(plan=plan, requirement__major=major,
                                                                   requirement__is_credit_requirement=False)
                serializer = self.get_serializer(plan_requirements, many=True)
                requirements = serializer.data
                result_list.append({"major_name": major.major_name,
                                    "major_type": major.major_type,
                                    "requirements": requirements})
        else:
            return Response({"error": "search_type not_allowed"}, status=status.HTTP_400_BAD_REQUEST)

        data = {"majors": result_list}
        return Response(data, status=status.HTTP_200_OK)

    # PUT /requirement/
    def put(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        update_list = request.data.copy()
        if update_list:
            plan_id = update_list[0]['plan_id']
            try:
                plan = Plan.objects.get(pk=plan_id)
            except Plan.DoesNotExist:
                return Response({"error": "plan_id not_exist"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "update_list missing"}, status=status.HTTP_400_BAD_REQUEST)

        for curr_request in update_list:
            requirement_id = curr_request['requirement_id']
            is_fulfilled = curr_request['is_fulfilled']

            requirement = Requirement.objects.get(pk=requirement_id)
            planrequirement = PlanRequirement.objects.filter(plan=plan, requirement=requirement)
            planrequirement.update(is_fulfilled=is_fulfilled)

        majors = Major.objects.filter(planmajor__plan=plan)

        result_list = []
        for major in list(majors):
            planrequirement = PlanRequirement.objects.filter(plan=plan, requirement__major=major)
            serializer = RequirementSerializer(planrequirement, many=True)
            requirements = serializer.data
            result_list.append({"major_name": major.major_name,
                                "major_type": major.major_type,
                                "requirements": requirements})

        data = {"majors": result_list}
        return Response(data, status=status.HTTP_200_OK)

    # GET /requirement/progress/
    @action(detail=False, methods=['GET'])
    def progress(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.query_params.get('plan_id', None)

        if plan_id is None:
            return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "plan not_exist"}, status=status.HTTP_404_NOT_FOUND)

        planmajors = PlanMajor.objects.filter(plan=plan)

        result_list = []
        for planmajor in list(planmajors):
            serializer = ProgressSerializer(planmajor)
            progress = serializer.data
            result_list.append(progress)

        data = {"majors": result_list}
        return Response(data, status=status.HTTP_200_OK)