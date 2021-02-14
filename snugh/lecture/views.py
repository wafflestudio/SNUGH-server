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
        return Response(serializer.data, status=status.HTTP_201_CREATED) # Edit API Document 

    # PUT /plan 
    def update(self, request, pk=None):
        plan = self.get_object()
        data = request.data.copy()
        serializer = self.get_serializer(plan, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        # serializer.update(plan, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DEL /plan
    def destroy(self, request, pk=None):
        self.get_object().delete()
        return Response(status=status.HTTP_200_OK)

    # GET /plan 
    def retrieve(self, request, pk=None):
        plan = self.get_object() 
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
        return Response(serializer.data, status=status.HTTP_201_CREATED) # Edit API Document 

    # PUT /semester

    # DEL /semester

    # GET /semester

class LectureViewSet(viewsets.GenericViewSet):
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer 

    # POST /lecture
    def create(self, request):
        data = request.data.copy() 
        serializer = self.get_serializer(data=data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED) # Edit API Document 

    # PUT /lecture

    # DEL /lecture

    # GET /lecture