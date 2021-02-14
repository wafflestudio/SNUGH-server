from django.shortcuts import render
from rest_framework import status, viewsets, filters 
from rest_framework.response import Response
from lecture.models import Plan, Semester, Lecture 
from lecture.serializers import PlanSerializer, SemesterSerializer, LectureSerializer

# Create your views here.

class PlanViewSet(viewsets.GenericViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    # POST /plan
    def create(self, request):
        data = request.data.copy() 
        serializer = self.get_serializer(data=data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED) 

    # PUT /plan 
    def update(self, request, pk=None):
        plan = self.get_object()
        data = request.data.copy()
        serializer = self.get_serializer(plan, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(plan, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DEL /plan
    def destroy(self, request, pk=None):
        self.get_object().delete()
        return Response(status=status.HTTP_200_OK) # Need body or edit API document

    # GET /plan 
    def retrieve(self, request, pk=None):
        plan_id = request.query_params.get("plan_id")
        plan = Plan.objects.get(id=plan_id)
        return Response(self.get_serializer(plan), status=status.HTTP_200_OK)

class SemesterViewSet(viewsets.GenericViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer 

    # POST /semester
    def create(self, request):
        data = request.data.copy() 
        serializer = self.get_serializer(data=data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED) 

    # PUT /semester
    def update(self, request, pk=None):
        # SemesterLecture 
        semester = self.get_object()
        data = request.data.copy()
        serializer = self.get_serializer(semester, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semester, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DEL /semester
    def destroy(self, request, pk=None):
        self.get_object().delete()
        return Response(status=status.HTTP_200_OK) # Need body or edit API document

    # GET /semester
    def retrieve(self, request, pk=None):
        plan_id = request.query_params.get("plan_id")
        semester_id = request.query_params.get("semester_id")
        plan = Plan.objects.get(id=plan_id)
        semester = Semester.objects.get(id=semester_id, plan=plan)
        return Response(self.get_serializer(semester), status=status.HTTP_200_OK)

class LectureViewSet(viewsets.GenericViewSet):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer 

    # POST /lecture
    def create(self, request):
        # SemesterLecture
        data = request.data.copy() 
        serializer = self.get_serializer(data=data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED) 

    # PUT /lecture
    def update(self, request, pk=None):
        pass # SemesterLecture

    # DEL /lecture
    def destroy(self, request, pk=None):
        pass # SemesterLecture 

    # GET /lecture
    def retrieve(self, request, pk=None):
        pass 