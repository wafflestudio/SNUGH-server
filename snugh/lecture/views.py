from django.shortcuts import render 
from rest_framework import status, viewsets, filters
from rest_framework.response import Response 
from lecture.models import Plan, Semester, Lecture, SemesterLecture, MajorLecture   
from lecture.serializers import PlanSerializer, SemesterSerializer, LectureSerializer, SemesterLectureSerializer

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
    
    # PUT /plan/(int)
    def update(self, request, pk=None):
        plan = self.get_object() 
        data = request.data.copy() 
        serializer = self.get_serializer(plan, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(plan, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /plan/(int)
    def destroy(self, request, pk=None):
        self.get_object().delete()
        return Response(status=status.HTTP_200_OK)
    
    # GET /plan/(int)
    def retrieve(self, request, pk=None):
        plan = self.get_object() 
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK) # Add majors, semester credits in Response body

    # GET /plan
    def list(self, request):
        plans = self.get_queryset()
        return Response(self.get_serializer(plans, many=True).data, status=status.HTTP_200_OK) 

class SemesterViewSet(viewsets.GenericViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer 

    # POST /semester/?plan_id=(int)
    def create(self, request): 
        plan_id = request.query_params.get("plan_id")
        data = request.data.copy()
        data['plan'] = plan_id 
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED) # Change body to include all semesters in the plan
    
    # PUT /semester/(int)/?plan_id=(int)
    def update(self, request, pk=None):
        # Check SemesterLecture 
        plan_id = request.query_params.get("plan_id")
        plan = Plan.objects.get(id=plan_id)
        semester = self.get_object()
        data = request.data.copy() 
        serializer = self.get_serializer(semester, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semester, serializer.validated_data)
        
        serializer = PlanSerializer(plan) 
        return Response(serializer.data, status=status.HTTP_200_OK) # Different body 
    
    # DEL /semester/(int)/?plan_id=(int) 
    def destroy(self, request, pk=None):
        plan_id = request.query_params.get("plan_id")
        plan = Plan.objects.get(id=plan_id)
        self.get_object().delete() 
        serializer = PlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK) 
    
    # GET /semester/(int)
    def retrieve(self, request, pk=None):
        semester = self.get_object() 
        serializer = self.get_serializer(semester)
        return Response(serializer.data, status=status.HTTP_200_OK) 

class LectureViewSet(viewsets.GenericViewSet):
    queryset = Lecture.objects.all()
    serializer_class = SemesterLectureSerializer 

    # POST /lecture/?plan_id=(int)&semester_id=(int)
    def create(self, request): 
        plan_id = request.query_params.get("plan_id")
        semester_id = request.query_params.get("semester_id")
        semester = Semester.objects.get(id=semester_id) 

        data = request.data.copy() 
        lecture_id_list = data['lecture_id']
        
        for lecture_id in lecture_id_list:
            lecture = Lecture.objects.get(id=lecture_id) 
            majorlecture = MajorLecture.objects.get(lecture=lecture)
            SemesterLecture.objects.create(semester=semester, lecture=lecture, lecture_type=majorlecture.lecture_type, lecture_type_detail=majorlecture.lecture_type_detail, lecture_type_detail_detail=majorlecture.lecture_type_detail_detail, recent_sequence=0) # Take care of recent_sequence

        semesterlectures = SemesterLecture.objects.filter(semester=semester) 

        ls = []
        for semesterlecture in semesterlectures:
            lecture = semesterlecture.lecture
            ls.append({
                "id": lecture.id,
                "lecture_name": lecture.lecture_name,
                "credit": lecture.credit,
                "is_open": lecture.is_open,
                "open_semester": lecture.open_semester, 
            })

        body = {
            "plan": int(plan_id), 
            "semester": int(semester_id),
            "lectures": ls, 
        }
        return Response(body, status=status.HTTP_201_CREATED) 
    
    # PUT /lecture/?plan_id=(int)&semester_id=(int)&lecture_id=(int)
    def put(self, request):
        plan_id = request.query_params.get("plan_id")
        plan = Plan.objects.get(id=plan_id)
        semester_id = request.query_params.get("semester_id")
        semester = Semester.objects.get(id=semester_id) 
        lecture_id = request.query_params.get("lecture_id")
        lecture = Lecture.objects.get(id=lecture_id)
        semesterlecture = SemesterLecture.objects.get(semester=semester, lecture=lecture) 

        data = request.data.copy() 
        new_semester_id = data['semester_id']
        new_semester = Semester.objects.get(id=new_semester_id)
        semesterlecture.semester = new_semester 
        semesterlecture.save() 

        ls = [] 
        semesters = Semester.objects.filter(plan=plan)
        for semester in semesters: 
            ls.append(SemesterSerializer(semester).data)
        
        body = {
            "plan": int(plan_id),
            "semesters": ls,
        }

        return Response(body, status=status.HTTP_200_OK) # Check semester_type 

    # DEL /lecture/?plan_id=(int)&semester_id=(int)&lecture_id=(int)
    def destroy(self, request, pk=None):
        plan_id = request.query_params.get("plan_id")
        semester_id = request.query_params.get("semester_id")
        semester = Semester.objects.get(id=semester_id)
        lecture_id = request.query_params.get("lecture_id")
        lecture = Lecture.objects.get(id=lecture_id)
        semesterlecture = SemesterLecture.objects.get(semester=semester, lecture=lecture)
        semesterlecture.delete() 

        semesterlectures = SemesterLecture.objects.filter(semester=semester)

        ls = [] 
        for semesterlecture in semesterlectures: 
            lecture = semesterlecture.lecture 
            ls.append({
                "id": lecture.id,
                "lecture_name": lecture.lecture_name,
                "credit": lecture.credit,
                "is_open": lecture.is_open,
                "open_semester": lecture.open_semester,
            })
        
        body = {
            "plan": int(plan_id),
            "semester": int(semester_id),
            "lectures": ls,
        }

        return Response(body, status=status.HTTP_200_OK) 

    # GET /lecture/?lecture_type=(int)&search=(string)
    def retrieve(self, request, pk=None):
        # lecture_type = request.query_params.get("lecture_type")
        # search_keyword = request.query_params.get("search")
        pass 
