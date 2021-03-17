from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from requirement.models import Requirement, PlanRequirement
from requirement.serializers import RequirementSerializer, ProgressSerializer
from lecture.models import Plan


class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer

    # GET /requirement/
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.query_params.get('plan_id')
        search_type = request.query_params.get('search_type')

        if not plan_id:
            return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)
        if not search_type:
            return Response({"error": "search_type missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "plan_id not_exist"}, status=status.HTTP_404_NOT_FOUND)

        if search_type == "all":
            plan_requirements = PlanRequirement.objects.filter(plan=plan)
        elif search_type == "credit":
            plan_requirements = PlanRequirement.objects.filter(plan=plan, requirement__is_credit_requirement=True)
        elif search_type == "etc":
            plan_requirements = PlanRequirement.objects.filter(plan=plan, requirement__is_credit_requirement=False)
        else:
            return Response({"error": "search_type not_allowed"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(plan_requirements, many=True)
        data = serializer.data
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

        planrequirement = PlanRequirement.objects.filter(plan=plan)
        serializer = RequirementSerializer(planrequirement, many=True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # GET /requirement/progress/
    @action(detail=False, methods=['GET'])
    def progress(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.query_params.get('plan_id')

        if not plan_id:
            return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "plan_id not_exist"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProgressSerializer(plan)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)