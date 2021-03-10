from django.shortcuts import render 
from rest_framework import status, viewsets, filters
from rest_framework.response import Response 
from lecture.models import * 
from lecture.serializers import *
from user.models import *
from rest_framework.decorators import action

class PlanViewSet(viewsets.GenericViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer 

    # POST /plan
    def create(self, request):
        major_id = request.query_params.get("major_id", None)
        #err response 1
        if major_id is None:
            return Response({"error":"major_id missing"}, status=status.HTTP_400_BAD_REQUEST)    
        #err response 2
        try:
            major = Major.objects.get(id=major_id)
        except Major.DoesNotExist:
            return Response({"error":"No major matching the given major_id and plan id"}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy() 
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save() 
        plan_id = serializer.data["id"]
        plan = Plan.objects.get(id=plan_id)
        PlanMajor.objects.create(plan=plan, major=major)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # PUT /plan/(int)
    def update(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        plan = self.get_object() 
        data = request.data.copy() 
        serializer = self.get_serializer(plan, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(plan, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /plan/(int)
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        self.get_object().delete()
        return Response(status=status.HTTP_200_OK)
    
    # GET /plan/(int)
    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        plan = self.get_object() 
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /plan
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        plans = Plan.objects.filter(user=user)
        return Response(self.get_serializer(plans, many=True).data, status=status.HTTP_200_OK)

    # POST/GET/DELETE /plan/major
    @action(detail=True, methods=['POST', 'DELETE', 'GET'])    
    def major(self, request, pk=None):    
        plan_id=request.query_params.get("plan_id")
        plan=Plan.objects.get(id=plan_id)

        #err response 1
        if not bool(plan_id):
            return Response({"error":"plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)    

        #GET planmajor
        if self.request.method == 'GET':
            planmajor=PlanMajor.objects.filter(plan=plan)
        else:
            major_id=request.query_params.get("major_id")

            #err response 2
            if not bool(major_id):
                return Response({"error":"major_id missing"}, status=status.HTTP_400_BAD_REQUEST)    
            #err response 3
            try:
                major=Major.objects.get(id=major_id)
            except Major.DoesNotExist:
                return Response({"error":"No major matching the given major_id and plan id"}, status=status.HTTP_404_NOT_FOUND)

            #POST planmajor
            if self.request.method == 'POST':
                PlanMajor.objects.create(plan=plan, major=major)
            #DELETE planmajor
            elif self.request.method == 'DELETE':
                planmajor=PlanMajor.objects.get(plan=plan, major=major)
                planmajor.delete()            

            planmajor=PlanMajor.objects.filter(plan=plan)

        #main response            
        ls=[]
        for major in planmajor.major.all():
            ls.append({"id":major.id, "name":major.major_name, "type":major.major_type})        
        body={"plan_id":plan.id, "major":ls}
        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)

class SemesterViewSet(viewsets.GenericViewSet):
    queryset = Semester.objects.all()
    serializer_class = SimpleSemesterSerializer 

    # POST /semester
    def create(self, request): 
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # PUT /semester/(int)
    def update(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        semester = self.get_object()
        data = request.data.copy() 
        serializer = self.get_serializer(semester, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semester, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /semester/(int)
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        self.get_object().delete() 
        return Response(status=status.HTTP_200_OK)
    
    # GET /semester/(int)
    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        semester = self.get_object() 
        serializer = SemesterSerializer(semester)
        return Response(serializer.data, status=status.HTTP_200_OK) 

class LectureViewSet(viewsets.GenericViewSet):
    queryset = SemesterLecture.objects.all()
    search_fields = ['lecture_name']
    filter_backends = (filters.SearchFilter, )
    serializer_class = SemesterLectureSerializer 

    # POST /lecture
    def create(self, request): 
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        semester_id = request.data.get('semester_id')
        lecture_id_list = request.data.get('lecture_id') 
        recent_sequence_list = request.data.get('recent_sequence')
        semester = Semester.objects.get(id=semester_id) 
        
        for i in range(len(lecture_id_list)): 
            lecture = Lecture.objects.get(id=lecture_id_list[i]) 
            majorlecture = MajorLecture.objects.get(lecture=lecture)
            SemesterLecture.objects.create(semester=semester, lecture=lecture, lecture_type=majorlecture.lecture_type, lecture_type_detail=majorlecture.lecture_type_detail, lecture_type_detail_detail=majorlecture.lecture_type_detail_detail, recent_sequence=recent_sequence_list[i]) 

        semesterlectures = SemesterLecture.objects.filter(semester=semester) 
        ls = [] 
        for semesterlecture in semesterlectures:
            lecture = semesterlecture.lecture
            ls.append({
                "lecture_id": lecture.id, 
                "semester_lecture_id": semesterlecture.id, 
                "lecture_name": lecture.lecture_name,
                "credit": lecture.credit, 
                "is_open": lecture.is_open, 
                "open_semester": lecture.open_semester, 
            })

        body = {
            "plan": int(semester.plan.id),
            "semester": int(semester_id),
            "lectures": ls, 
        }
        return Response(body, status=status.HTTP_201_CREATED) 
    
    # PUT /lecture/(int)
    def update(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        semesterlecture = self.get_object()
        data = request.data.copy() 
        serializer = self.get_serializer(semesterlecture, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semesterlecture, serializer.validated_data) 
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DEL /lecture/(int) 
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        self.get_object().delete()
        return Response(status=status.HTTP_200_OK) 

    # GET /lecture/?lecture_type=(int)&search_keyword=(string)
    def list(self, request): 
        queryset = self.get_queryset() 
        lecture_type = request.query_params.get("lecture_type", None)
        search_keyword = request.query_params.get("search_keyword", None)
        if lecture_type is not None:
            queryset = queryset.filter(lecture_type=lecture_type)
        filter_backends = self.filter_queryset(queryset) 

        lectures = set() 
        for semesterlecture in filter_backends:
            lecture = Lecture.objects.get(semesterlecture=semesterlecture)
            if search_keyword is None:
                lectures.add(lecture)
            elif search_keyword in lecture.lecture_name:
                lectures.add(lecture) 
        ls = [] 
        for lecture in lectures:
            ls.append(LectureSerializer(lecture).data)
        body = {
            "lectures": ls,
        }
        # page = self.paginate_queryset(filter_backends)
        # return self.get_paginated_response(serializer.data) 
        return Response(body, status=status.HTTP_200_OK) 
