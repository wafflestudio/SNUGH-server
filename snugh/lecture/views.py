from django.shortcuts import render
from rest_framework import status, viewsets, filters 
from rest_framework.response import Response
from lecture.models import Plan, Semester, Lecture 

# Create your views here.

class PlanViewSet(viewsets.GenericViewSet):
    queryset = Plan.objects.all()

    # POST /plan
    def create(self, request):
        data = request.data.copy() 
        serializer = self.get_serializer(data=data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED) # Edit API Document 

    # PUT /plan 

    # DEL /plan

    # GET /plan 

class SemesterViewSet(viewsets.GenericViewSet):
    queryset = Semester.objects.all()

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