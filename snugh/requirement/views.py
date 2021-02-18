from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from requirement.models import Requirement, PlanRequirement
from requirement.serializers import RequirementSerializer, ProgressSerializer
from lecture.models import Plan


class RequirementViewSet(viewsets.GenericViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer

    # GET /requirement
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        requirements = self.get_object()

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
                requirements = requirements.planrequirement.filter(plan_id=plan_id)
                requirements = requirements.filter(is_credit_requirement=True)
                plan_requirements = requirements.planrequirement
            elif search_type == "etc":
                requirements = requirements.planrequirement.filter(plan_id=plan_id)
                requirements = requirements.filter(is_credit_requirement=False)
                plan_requirements = requirements.planrequirement
            else:
                return Response({"error": "wrong search_type."}, status=status.HTTP_400_BAD_REQUEST)
        except Plan.DoesNotExist:
            return Response({"error": "wrong plan_id"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(plan_requirements, many=True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # PUT /requirement
    def update(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()

        plan_requirements = PlanRequirement.objects.all()
        serializer = RequirementSerializer(plan_requirements, data=data, many=True, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(plan_requirements, serializer.validated_data)

        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # GET /requirement/progress
    def progress(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

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