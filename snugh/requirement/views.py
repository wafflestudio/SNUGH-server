from django.shortcuts import render
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

        plan_id = request.query_params.get('plan_id')
        search_type = request.query_params.get('type')

        if not plan_id:
            return Response({"error": "plan_id missing."}, status=status.HTTP_400_BAD_REQUEST)
        if not search_type:
            return Response({"error": "search_type missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(pk=plan_id)

            if search_type == "all":
                requirements = None # 작업중
            elif search_type == "credit":
                requirements = None # 작업중
            elif search_type == "etc":
                requirements = None # 작업중
            else:
                return Response({"error": "wrong search_type."}, status=status.HTTP_400_BAD_REQUEST)
        except Plan.DoesNotExist:
            return Response({"error": "wrong plan_id"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(requirements, many=True)
        data = serializer.data
        return Response(data, status=status.HTTP_200_OK)

    # PUT /requirement

    # GET /requirement/progress
