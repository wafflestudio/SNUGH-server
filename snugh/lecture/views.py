from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction
from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from lecture.models import * 
from lecture.serializers import *
from user.models import *
from requirement.models import *


class PlanViewSet(viewsets.GenericViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer 

    # POST /plan/
    @transaction.atomic
    def create(self, request):
        user = request.user

        # err response
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        plan_name = data.get("plan_name", None)
        majors = data.get("majors", None)

        # err response
        if majors is None:
            return Response({"error": "majors missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            for major in majors:
                searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
        except Major.DoesNotExist:
            return Response({"error": "major not_exist"}, status=status.HTTP_404_NOT_FOUND)

        plan = Plan.objects.create(user=user, plan_name=plan_name)

        # planmajor
        if len(majors) == 1 and majors[0]['major_type'] == Major.MAJOR:
            searched_major = Major.objects.get(major_name=majors[0]['major_name'], major_type=Major.SINGLE_MAJOR)
            PlanMajor.objects.create(plan=plan, major=searched_major)
        else:
            for major in majors:
                searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
                PlanMajor.objects.create(plan=plan, major=searched_major)

        # planrequirement
        for major in majors:
            curr_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            requirements = Requirement.objects.filter(major= curr_major)
            for requirement in requirements:
                PlanRequirement.objects.create(plan=plan, requirement=requirement)

        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /plan/(int)/
    @transaction.atomic
    def update(self, request, pk=None):
        user = request.user

        # err response
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        plan = Plan.objects.get(pk=pk)
        serializer = self.get_serializer(plan, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(plan, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /plan/(int)/
    @transaction.atomic
    def destroy(self, request, pk=None):
        user = request.user

        # err response
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = Plan.objects.get(pk=pk)
        plan.delete()
        return Response(status=status.HTTP_200_OK)

    # GET /plan/(int)/
    @transaction.atomic
    def retrieve(self, request, pk=None):
        user = request.user

        # err response
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = Plan.objects.get(pk=pk)
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /plan/
    @transaction.atomic
    def list(self, request):
        user = request.user

        # err response
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plans = Plan.objects.filter(user=user)
        return Response(self.get_serializer(plans, many=True).data, status=status.HTTP_200_OK)

    # GET/PUT /plan/major/
    @action(detail=False, methods=['GET', 'PUT'])
    @transaction.atomic
    def major(self, request):
        user = request.user

        # err response
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.query_params.get("plan_id")

        # err response
        if not bool(plan_id):
            return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)
        if Plan.objects.filter(id=plan_id).exists():
            plan = Plan.objects.get(id=plan_id)
        else:
            return Response({"error": "plan not_exist"}, status=status.HTTP_404_NOT_FOUND)

        # GET /plan/major/
        if self.request.method == 'GET':
            planmajor = PlanMajor.objects.filter(plan=plan)

        # PUT /plan/major/
        elif self.request.method == 'PUT':
            post_list = request.data.get("post_list", None)
            delete_list = request.data.get("delete_list", None)

            # err response
            if post_list is None:
                return Response({"error": "post_list missing"}, status=status.HTTP_400_BAD_REQUEST)
            if delete_list is None:
                return Response({"error": "delete_list missing"}, status=status.HTTP_400_BAD_REQUEST)

            # planmajor
            for major in delete_list:
                major_name = major['major_name']
                major_type = major['major_type']
                selected_major = Major.objects.get(major_name=major_name, major_type=major_type)
                selected_planmajor = PlanMajor.objects.get(plan=plan, major=selected_major)
                selected_planmajor.delete()

            for major in post_list:
                major_name = major['major_name']
                major_type = major['major_type']
                selected_major = Major.objects.get(major_name=major_name, major_type=major_type)
                PlanMajor.objects.create(plan=plan, major=selected_major)

            # planrequirement
            for major in post_list:
                curr_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
                requirements = Requirement.objects.filter(major=curr_major)
                for requirement in requirements:
                    PlanRequirement.objects.create(plan=plan, requirement=requirement)

            for major in delete_list:
                curr_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
                requirements = Requirement.objects.filter(major=curr_major)
                for requirement in requirements:
                    selected_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=requirement)
                    selected_planrequirement.delete()


            update_plan_info(plan)

        # main response
        body = self.get_serializer(plan).data

        if self.request.method == 'POST':
            return Response(body, status=status.HTTP_201_CREATED)
        else:
            return Response(body, status=status.HTTP_200_OK)


class SemesterViewSet(viewsets.GenericViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer

    # POST /semester/
    @transaction.atomic
    def create(self, request): 
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = request.data.get('plan', None)
        year = request.data.get('year', None)
        semester_type = request.data.get('semester_type', None)
        is_complete = request.data.get('is_complete', False)

        if plan is None:
            return Response({"error": "plan missing"}, status=status.HTTP_400_BAD_REQUEST)
        if year is None:
            return Response({"error": "year missing"}, status=status.HTTP_400_BAD_REQUEST)
        if semester_type is None:
            return Response({"error": "semester_type missing"}, status=status.HTTP_400_BAD_REQUEST)
        if Semester.objects.filter(plan=plan, year=year, semester_type=semester_type, is_complete=is_complete).exists():
            return Response({"error": "semester already_exist"}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /semester/(int)/
    @transaction.atomic
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
    
    # DEL /semester/(int)/
    @transaction.atomic
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        semester = self.get_object()
        plan = semester.plan
        semester.delete()
        # update_plan_info(plan=plan)
        return Response(status=status.HTTP_200_OK)
    
    # GET /semester/(int)/
    @transaction.atomic
    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        semester = self.get_object() 
        serializer = SemesterSerializer(semester)
        return Response(serializer.data, status=status.HTTP_200_OK) 


class LectureViewSet(viewsets.GenericViewSet):
    queryset = SemesterLecture.objects.all()
    serializer_class = SemesterLectureSerializer

    # POST /lecture
    # 에러 처리: 이미 있는 lecture 추가시 IntegrityError 500 -> BadRequest
    # 에러 처리: 똑같은 Lecture가 body에 두번 있으면 -> for문 들어가기도 전에 에러처리해야.
    @transaction.atomic
    def create(self, request): 
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        semester_id = request.data.get('semester_id')
        lecture_id_list = request.data.get('lecture_id') 
#        recent_sequence_list = request.data.get('recent_sequence')
        lecture_type_list = request.data.get('lecture_type')
        recognized_major_id_list = request.data.get('recognized_major_id')
        semester = Semester.objects.get(id=semester_id)

        if(len(lecture_id_list) != len(set(lecture_id_list))):
            return Response({"error": "identical lectures in lecture_id_list"}, status=status.HTTP_400_BAD_REQUEST)

        for i in range(len(lecture_id_list)):
            lecture = Lecture.objects.get(id=lecture_id_list[i]) 
            lecture_type = lecture_type_list[i]
            recognized_major_id = recognized_major_id_list[i]
            recognized_major = Major.objects.get(id=recognized_major_id)

            SemesterLecture.objects.create(recognized_major=recognized_major, semester=semester, lecture=lecture, lecture_type=lecture_type, recent_sequence = 20)
            semlecture = SemesterLecture.objects.get(semester=semester, lecture=lecture)
            semlecture.recent_sequence = semlecture.id
            semlecture.save()

            if lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
                semester.major_requirement_credit += lecture.credit
                semester.save()
            elif lecture_type == SemesterLecture.MAJOR_ELECTIVE or lecture_type == SemesterLecture.TEACHING:
                # credit = semester.major_elective_credit
                # credit += lecture.credit
                # semester.objects.update(partial=True, major_elective_credit=credit)
                semester.major_elective_credit += lecture.credit
                semester.save()
            elif lecture_type == SemesterLecture.GENERAL:
                semester.general_credit += lecture.credit
                semester.save()
            elif lecture_type == SemesterLecture.GENERAL_ELECTIVE:
                semester.general_elective_credit += lecture.credit
                semester.save()

        semesterlectures = SemesterLecture.objects.filter(semester=semester)

            # semesterlecture.objects.update(partial=True, recent_sequence = semesterlecture.id)
        # 정렬시
        # sorted_list = sorted(list(semesterlectures), key=lecture_type_to_int)
        #
        # for i in range(len(sorted_list)):
        #     semesterlecture = sorted_list[i]
        #     semesterlecture.update(partial=True, recent_sequence=i)

        data = SemesterSerializer(semester).data
        # ls = []
        # for semesterlecture in semesterlectures:
        #     lecture = semesterlecture.lecture
        #     ls.append({
        #         "lecture_id": lecture.lecture_id,
        #         "semester_lecture_id": semesterlecture.id,
        #         "recent_sequence" : semesterlecture.recent_sequence,
        #         "lecture_name": lecture.lecture_name,
        #         "credit": lecture.credit,
        #         "open_semester": lecture.open_semester,
        #     })
        #
        # body = {
        #     "plan": int(semester.plan.id),
        #     "semester": int(semester_id),
        #     "major_requrirement" : int(semester.major_requirement_credit),
        #     "major_elective": int(semester.major_elective_credit),
        #     "general": int(semester.general_credit),
        #     "general_elective": int(semester.general_elective_credit),
        #     "lectures": ls,
        # }
        return Response(data, status=status.HTTP_201_CREATED)
    
    # PUT /lecture/(int)
    @transaction.atomic
    def update(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        lecture = get_object_or_404(Lecture, pk=pk)
        semester_from_id = request.data.get('semester_from_id')
        semester_to_id = request.data.get('semester_to_id')
        semester_from_list = request.data.get('semester_from')
        semester_to_list = request.data.get('semester_to')

        semester_to = Semester.objects.get(id=semester_to_id)
        semester_from = Semester.objects.get(id=semester_from_id)

        # credit 처리 및 semesterlecture의 semester 변경(?)
        semesterlecture = SemesterLecture.objects.get(semester_id=semester_from_id, lecture_id=lecture.id)
        subtract_credits(semesterlecture)

        semesterlecture.semester = semester_to
        semesterlecture.save()
        add_credits(semesterlecture)

        # recent sequence 저장
        for i in range(len(semester_from_list)):
            semester_lecture = SemesterLecture.objects.get(semester_id=semester_from_id, lecture_id=semester_from_list[i])
            semester_lecture.recent_sequence = i
            semester_lecture.save()

        for i in range(len(semester_to_list)):
            semester_lecture2 = SemesterLecture.objects.get(semester_id=semester_to_id, lecture_id=semester_to_list[i])
            semester_lecture2.recent_sequence = i
            semester_lecture2.save()

        serializer = SemesterSerializer([semester_to,semester_from], many=True)
        data = serializer.data

        return Response(data, status=status.HTTP_200_OK)

    # PUT /lecture/{lecture_id}/recognized_major/
    @action(methods=['PUT'], detail=True)
    def recognized_major(self, request, pk=None):
        lecture = self.get_object() 
        lecture_type = request.data.get('lecture_type', None) 
        # Case 1: lecture_type를 교양으로 변경
        if lecture_type == 'general':
            data = {
                "lecture_type": lecture_type
            }
            serializer = self.get_serializer(lecture, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(lecture, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Case 2: 학과별 강의 구분을 recognized_major1,2와 lecture_type1,2를 이용해 입력  
        elif lecture_type == 'major_requirement' or lecture_type == 'major_elective':
            recognized_major1 = Major.objects.get(major_name=request.data.get('recognized_major_name1', None), major_type=request.data.get('recognized_major_type1', None))
            recognized_major2 = Major.objects.get(major_name=request.data.get('recognized_major_name2', None), major_type=request.data.get('recognized_major_type2', None))
            lecture_type1 = request.data.get('lecture_type1', None) 
            lecture_type2 = request.data.get('lecture_type2', None) 
            data = {
                "lecture_type": lecture_type, 
                "recognized_major1": recognized_major1.id,
                "recognized_major2": recognized_major2.id,
                "lecture_type1": lecture_type1, 
                "lecture_type2": lecture_type2 ,
            }
            serializer = self.get_serializer(lecture, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(lecture, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Case 3: lecture_type를 general_elective로 변경 
        elif lecture_type == 'general_elective':
            data = {
                "lecture_type": lecture_type
            }
            serializer = self.get_serializer(lecture, data=data, partial=True) 
            serializer.is_valid(raise_exception=True)
            serializer.update(lecture, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK) 

        else:
            return Response({"error": "wrong lecture_type"}, status=status.HTTP_400_BAD_REQUEST)

    # DEL /lecture/(int)
    @transaction.atomic
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        semesterlecture = SemesterLecture.objects.get(pk=pk)
        subtract_credits(semesterlecture)

        semesterlecture.delete()
        return Response(status=status.HTTP_200_OK) 

    # GET /lecture/?search_type=(string)&search_keyword=(string)&major=(string)&credit=(string)
    def list(self, request): 
        search_type = request.query_params.get("search_type", None)
        # Case 1: major requirement or major elective
        if search_type == 'major_requirement' or search_type == 'major_elective':
            major = request.query_params.get("major", None)
            if major: 
                majorLectures = MajorLecture.objects.filter(major=major, lecture_type=search_type)
                lectures = Lecture.objects.filter(majorlecture__in=majorLectures)
                serializer = LectureSerializer(lectures, many=True) 
                return Response(serializer.data, status = status.HTTP_200_OK)
            else: 
                return Response({"error": "major missing"}, status=status.HTTP_400_BAD_REQUEST)
        # Case 2: general
        elif search_type == 'general': 
            credit = request.query_params.get("credit", None)
            search_keyword = request.query_params.get("search_keyword", None)
            if credit and search_keyword:
                lectures = Lecture.objects.filter(credit=credit, lecture_name__icontains=search_keyword) 
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status = status.HTTP_200_OK)
            else:
                return Response({"error": "credit or search keyword missing"}, status=status.HTTP_400_BAD_REQUEST) 
        # Case 3: keyword 
        else:
            search_keyword = request.query_params.get("search_keyword", None)
            if search_keyword:  # 만약 검색어가 존재하면
                lectures = Lecture.objects.filter(lecture_name__icontains=search_keyword)  # 해당 검색어를 포함한 queryset 가져오기
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status = status.HTTP_200_OK)
            else:
                return Response({"error": "search keyword missing"}, status=status.HTTP_400_BAD_REQUEST)

# 공용 함수 모음 #
def update_plan_info(plan):
    # SemesterLecture 모델의 lecture_type 관련 값 업데이트
    majors = Major.objects.filter(planmajor__plan=plan)
    entrance_year = plan.user.userprofile.entrance_year
    semester_lectures = SemesterLecture.objects.filter(semester__plan=plan)
    for semester_lecture in list(semester_lectures):
        lecture = semester_lecture.lecture
        recognized_major, lecture_type = cal_lecture_type(lecture, majors, entrance_year)
        semester_lecture.recognized_major = recognized_major
        semester_lecture.lecture_type = lecture_type
        semester_lecture.save()

    # Semester 모델의 credit 관련 값 업데이트
    semesters = Semester.objects.filter(plan=plan)
    for semester in list(semesters):
        mr_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                             semesterlecture__lecture_type=SemesterLecture.MAJOR_REQUIREMENT)
        me_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                             semesterlecture__lecture_type=SemesterLecture.MAJOR_ELECTIVE)
        t_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                            semesterlecture__lecture_type=SemesterLecture.TEACHING)
        g_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                            semesterlecture__lecture_type=SemesterLecture.GENERAL)
        ge_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                             semesterlecture__lecture_type=SemesterLecture.GENERAL_ELECTIVE)
        mr_credit = 0
        me_credit = 0
        g_credit = 0
        ge_credit = 0

        for lecture in list(mr_lectures):
            mr_credit += lecture.credit
        for lecture in list(me_lectures):
            me_credit += lecture.credit
        for lecture in list(t_lectures):
            me_credit += lecture.credit
        for lecture in list(g_lectures):
            g_credit += lecture.credit
        for lecture in list(ge_lectures):
            ge_credit += lecture.credit

        semester.major_requirement_credit = mr_credit
        semester.major_elective_credit = me_credit
        semester.general_credit = g_credit
        semester.general_elective_credit = ge_credit
        semester.save()

    # PlanRequirement 모델의 earned_credit, is_fulfilled 업데이트
    majors = Major.objects.filter(planmajor__plan=plan)
    for major in list(majors):
        mr_r = Requirement.objects.get(major=major, requirement_type=Requirement.MAJOR_REQUIREMENT)
        me_r = Requirement.objects.get(major=major, requirement_type=Requirement.MAJOR_ELECTIVE)
        g_r = Requirement.objects.get(major=major, requirement_type=Requirement.GENERAL)
        ge_r = Requirement.objects.get(major=major, requirement_type=Requirement.GENERAL_ELECTIVE)

        mr_pr = PlanRequirement.objects.get(plan=plan, requirement__major=major,
                                            requirement__requirement_type=Requirement.MAJOR_REQUIREMENT)
        me_pr = PlanRequirement.objects.get(plan=plan, requirement__major=major,
                                            requirement__requirement_type=Requirement.MAJOR_ELECTIVE)
        g_pr = PlanRequirement.objects.get(plan=plan, requirement__major=major,
                                           requirement__requirement_type=Requirement.GENERAL)
        ge_pr = PlanRequirement.objects.get(plan=plan, requirement__major=major,
                                            requirement__requirement_type=Requirement.GENERAL_ELECTIVE)
        mr_credit = 0
        me_credit = 0
        g_credit = 0
        ge_credit = 0
        for semester in list(semesters):
            mr_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                                 semesterlecture__pivot_major=major,
                                                 semesterlecture__lecture_type=SemesterLecture.MAJOR_REQUIREMENT)
            me_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                                 semesterlecture__pivot_major=major,
                                                 semesterlecture__lecture_type=SemesterLecture.MAJOR_ELECTIVE)
            g_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                                semesterlecture__pivot_major=major,
                                                semesterlecture__lecture_type=SemesterLecture.GENERAL)
            ge_lectures = Lecture.objects.filter(semesterlecture__semester=semester,
                                                 semesterlecture__pivot_major=major,
                                                 semesterlecture__lecture_type=SemesterLecture.GENERAL_ELECTIVE)
            for lecture in list(mr_lectures):
                mr_credit += lecture.credit
            for lecture in list(me_lectures):
                me_credit += lecture.credit
            for lecture in list(g_lectures):
                g_credit += lecture.credit
            for lecture in list(ge_lectures):
                ge_credit += lecture.credit

        mr_pr.earned_credit = mr_credit
        mr_pr.save()
        me_pr.earned_credit = me_credit
        me_pr.save()
        g_pr.earned_credit = g_credit
        g_pr.save()
        ge_pr.earned_credit = ge_credit
        ge_pr.save()

        if mr_r.required_credit <= mr_pr.earned_credit:
            mr_pr.is_fulfilled = True
            mr_pr.save()
        if me_r.required_credit <= me_pr.earned_credit:
            me_pr.is_fulfilled = True
            me_pr.save()
        if g_r.required_credit <= g_pr.earned_credit:
            g_pr.is_fulfilled = True
            g_pr.save()
        if ge_r.required_credit <= ge_pr.earned_credit:
            ge_pr.is_fulfilled = True
            ge_pr.save()

def cal_lecture_type(lecture, majors, entrance_year):
    result_major = None
    result_lecture_type = None
    for major in list(majors):
        try:
            majorlecture = MajorLecture.objects.get(major=major,
                                                    lecture=lecture,
                                                    start_year__lte=entrance_year,
                                                    end_year__gte=entrance_year)
            if cal_priority_lt(majorlecture.lecture_type) > cal_priority_lt(result_lecture_type):
                result_major = majorlecture.major
                result_lecture_type = majorlecture.lecture_type
        except MajorLecture.DoesNotExist:
            pass
    return result_major, result_lecture_type

def cal_priority_lt(lecture_type):
    switcher = {
        SemesterLecture.MAJOR_REQUIREMENT: 4,
        SemesterLecture.MAJOR_ELECTIVE: 3,
        SemesterLecture.TEACHING: 3,
        SemesterLecture.GENERAL: 2,
        SemesterLecture.GENERAL_ELECTIVE: 1
    }
    return switcher.get(lecture_type, -1)

def lecture_type_to_int(semesterlecture):
    switcher ={
        SemesterLecture.MAJOR_REQUIREMENT : 1,
        SemesterLecture.MAJOR_ELECTIVE : 2,
        SemesterLecture.TEACHING : 3,
        SemesterLecture.GENERAL : 4,
        SemesterLecture.GENERAL_ELECTIVE : 5
    }
    return switcher.get(semesterlecture, -1) # -1은 에러

def add_credits(semesterlecture):
    semester = semesterlecture.semester
    if(semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT):
        semester.major_requirement_credit += semesterlecture.lecture.credit
        semester.save()
    elif(semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING ):
        semester.major_elective_credit += semesterlecture.lecture.credit
        semester.save()
    elif(semesterlecture.lecture_type == SemesterLecture.GENERAL):
        semester.general_credit += semesterlecture.lecture.credit
        semester.save()
    elif(semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE):
        semester.general_elective_credit += semesterlecture.lecture.credit
        semester.save()
    return

def subtract_credits(semesterlecture):
    semester = semesterlecture.semester
    if (semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT):
        semester.major_requirement_credit -= semesterlecture.lecture.credit
        semester.save()
    elif (semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING):
        semester.major_elective_credit -= semesterlecture.lecture.credit
        semester.save()
    elif (semesterlecture.lecture_type == SemesterLecture.GENERAL):
        semester.general_credit -= semesterlecture.lecture.credit
        semester.save()
    elif (semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE):
        semester.general_elective_credit -= semesterlecture.lecture.credit
        semester.save()
    return
