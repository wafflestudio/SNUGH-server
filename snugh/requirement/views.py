from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from requirement.models import Requirement, PlanRequirement
from requirement.serializers import RequirementSerializer, ProgressSerializer
from lecture.models import Plan
from user.models import Major


class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer

    # GET /requirement
    def list(self, request):
        user = request.user
        #if not user.is_authenticated:
        #    return Response(status=status.HTTP_401_UNAUTHORIZED)

        requirements = self.get_queryset()

        plan_id = request.query_params.get('plan_id')
        search_type = request.query_params.get('type')

        if not plan_id:
            return Response({"error": "plan_id missing."}, status=status.HTTP_400_BAD_REQUEST)
        if not search_type:
            return Response({"error": "search_type missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(pk=plan_id)

            if search_type == "all":
                plan_requirements = PlanRequirement.objects.filter(plan_id=plan_id)
            elif search_type == "credit":
                plan_requirements = PlanRequirement.objects.filter(plan_id=plan_id, requirement__is_credit_requirement=True)
            elif search_type == "etc":
                plan_requirements = PlanRequirement.objects.filter(plan_id=plan_id, requirement__is_credit_requirement=False)
            else:
                return Response({"error": "wrong search_type."}, status=status.HTTP_400_BAD_REQUEST)
        except Plan.DoesNotExist:
            return Response({"error": "wrong plan_id"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(plan_requirements, many=True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # PUT /requirement
    def put(self, request):
        return self.update(request)

    def update(self, request):
        user = request.user
        #if not user.is_authenticated:
        #    return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()

        plan_id = data[0]['plan_id']
        plan = Plan.objects.get(pk=plan_id)

        for curr in data:
            requirement_id = curr['requirement_id']
            is_fulfilled = curr['is_fulfilled']

            requirement = Requirement.objects.get(pk=requirement_id)
            planrequirement = PlanRequirement.objects.filter(plan_id=plan_id, requirement=requirement_id)
            planrequirement.update(is_fulfilled=is_fulfilled)

        planrequirement = PlanRequirement.objects.filter(plan=plan)
        serializer = RequirementSerializer(planrequirement, many=True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # GET /requirement/progress
    @action(detail=False, methods=['GET'])
    def progress(self, request):
        user = request.user
        #if not user.is_authenticated:
        #    return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.query_params.get('plan_id')

        if not plan_id:
            return Response({"error": "plan_id missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(pk=plan_id)
        except Plan.DoesNotExist:
            return Response({"error": "wrong plan_id"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProgressSerializer(plan)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)