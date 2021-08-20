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
from django.core.paginator import Paginator


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
            requirements = Requirement.objects.filter(major=curr_major,
                                                      start_year__lte=user.userprofile.entrance_year,
                                                      end_year__gte=user.userprofile.entrance_year)
            for requirement in requirements:
                PlanRequirement.objects.create(plan=plan, requirement=requirement, required_credit=requirement.required_credit)

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

    # 강의구분 자동계산
    # PUT /plan/(int)/calculate/
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def calculate(self, request, pk=None):
        user = request.user

        # err response
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = Plan.objects.get(pk=pk)

        semesters = Semester.objects.filter(plan=plan)
        semesterlectures =SemesterLecture.objects.filter(semester__in=semesters)
        majors = Major.objects.filter(planmajor__plan=plan)

        for semesterlecture in semesterlectures:
            # calculate lecture_type for each semesterlecture
            if semesterlecture.is_modified == False:
                semester = semesterlecture.semester
                lecture = semesterlecture.lecture
                # 전필, 전선, 교직, 일선 -> 교양 인 경우는 처리하지 못함!
                candidate_majorlectures = MajorLecture.objects.filter(lecture=lecture, major__in=majors,
                                                                      start_year__lte=user.userprofile.entrance_year,
                                                                      end_year__gt=user.userprofile.entrance_year).exclude(
                    lecture_type=MajorLecture.GENERAL).exclude(lecture_type = MajorLecture.GENERAL_ELECTIVE)
                # lecture_type = general or general_elective & not opened by majors
                if candidate_majorlectures.count() == 0:
                    # general_elective
                    if semesterlecture.lecture_type != SemesterLecture.GENERAL and semesterlecture.lecture_type != SemesterLecture.GENERAL_ELECTIVE:
                        prev_lecture_type1 = semesterlecture.lecture_type1
                        prev_lecture_type2 = semesterlecture.lecture_type2
                        # lecture_type 변경
                        semesterlecture.lecture_type = SemesterLecture.GENERAL_ELECTIVE
                        semesterlecture.lecture_type1 = SemesterLecture.GENERAL_ELECTIVE
                        semesterlecture.recognized_major1 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                        semesterlecture.lecture_type2 = SemesterLecture.NONE
                        semesterlecture.recognized_major2 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                        semesterlecture.save()
                        # semester credit 변경
                        semester.general_elective_credit += lecture.credit

                        if prev_lecture_type1 == SemesterLecture.MAJOR_REQUIREMENT:
                            semester.major_requirement_credit -= lecture.credit
                            semester.save()
                        elif prev_lecture_type1 == SemesterLecture.MAJOR_ELECTIVE or prev_lecture_type1 == SemesterLecture.TEACHING:
                            semester.major_elective_credit -= lecture.credit
                            semester.save()
                        elif prev_lecture_type1 == SemesterLecture.GENERAL:
                            semester.general_credit -= lecture.credit
                            semester.save()
                        elif prev_lecture_type1 == SemesterLecture.GENERAL_ELECTIVE:
                            semester.general_elective_credit -= lecture.credit
                            semester.save()

                        if prev_lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
                            semester.major_requirement_credit -= lecture.credit
                            semester.save()
                        elif prev_lecture_type2 == SemesterLecture.MAJOR_ELECTIVE or prev_lecture_type2 == SemesterLecture.TEACHING:
                            semester.major_elective_credit -= lecture.credit
                            semester.save()
                        elif prev_lecture_type2 == SemesterLecture.GENERAL:
                            semester.general_credit -= lecture.credit
                            semester.save()
                        elif prev_lecture_type2 == SemesterLecture.GENERAL_ELECTIVE:
                            semester.general_elective_credit -= lecture.credit
                            semester.save()
                    # general => 변경 필요 없음

                # 단수인정
                elif candidate_majorlectures.count() == 1:
                    majorlecture = candidate_majorlectures.first()

                    # lecture_type 변경
                    prev_lecture_type1 = semesterlecture.lecture_type1
                    prev_lecture_type2 = semesterlecture.lecture_type2

                    semesterlecture.lecture_type = majorlecture.lecture_type
                    semesterlecture.lecture_type1 = majorlecture.lecture_type
                    semesterlecture.recognized_major1 = majorlecture.major
                    semesterlecture.lecture_type2 = SemesterLecture.NONE
                    semesterlecture.recognized_major2 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                    semesterlecture.save()

                    # semester credit 변경
                    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
                        semester.major_requirement_credit += lecture.credit
                        semester.save()
                    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
                        semester.major_elective_credit += lecture.credit
                        semester.save()
                    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
                        semester.general_credit += lecture.credit
                        semester.save()
                    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
                        semester.general_elective_credit += lecture.credit
                        semester.save()

                    if prev_lecture_type1 == SemesterLecture.MAJOR_REQUIREMENT:
                        semester.major_requirement_credit -= lecture.credit
                        semester.save()
                    elif prev_lecture_type1 == SemesterLecture.MAJOR_ELECTIVE or prev_lecture_type1 == SemesterLecture.TEACHING:
                        semester.major_elective_credit -= lecture.credit
                        semester.save()
                    elif prev_lecture_type1 == SemesterLecture.GENERAL:
                        semester.general_credit -= lecture.credit
                        semester.save()
                    elif prev_lecture_type1 == SemesterLecture.GENERAL_ELECTIVE:
                        semester.general_elective_credit -= lecture.credit
                        semester.save()

                    if prev_lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
                        semester.major_requirement_credit -= lecture.credit
                        semester.save()
                    elif prev_lecture_type2 == SemesterLecture.MAJOR_ELECTIVE or prev_lecture_type2 == SemesterLecture.TEACHING:
                        semester.major_elective_credit -= lecture.credit
                        semester.save()
                    elif prev_lecture_type2 == SemesterLecture.GENERAL:
                        semester.general_credit -= lecture.credit
                        semester.save()
                    elif prev_lecture_type2 == SemesterLecture.GENERAL_ELECTIVE:
                        semester.general_elective_credit -= lecture.credit
                        semester.save()
                # 복수인정
                else:
                    cnt = 0
                    for majorlecture in candidate_majorlectures:
                        cnt += 1
                        # recognized_major1
                        if cnt == 1:
                            # lecture_type1 변경
                            prev_lecture_type1 = semesterlecture.lecture_type1

                            semesterlecture.lecture_type = majorlecture.lecture_type
                            semesterlecture.lecture_type1 = majorlecture.lecture_type
                            semesterlecture.recognized_major1 = majorlecture.major
                            semesterlecture.save()
                            # semester credit 변경
                            if prev_lecture_type1 == SemesterLecture.MAJOR_REQUIREMENT:
                                semester.major_requirement_credit -= lecture.credit
                                semester.save()
                            elif prev_lecture_type1 == SemesterLecture.MAJOR_ELECTIVE or prev_lecture_type1 == SemesterLecture.TEACHING:
                                semester.major_elective_credit -= lecture.credit
                                semester.save()
                            elif prev_lecture_type1 == SemesterLecture.GENERAL:
                                semester.general_credit -= lecture.credit
                                semester.save()
                            elif prev_lecture_type1 == SemesterLecture.GENERAL_ELECTIVE:
                                semester.general_elective_credit -= lecture.credit
                                semester.save()

                            if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
                                semester.major_requirement_credit += lecture.credit
                                semester.save()
                            elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
                                semester.major_elective_credit += lecture.credit
                                semester.save()
                        elif cnt ==2:
                            prev_lecture_type2 = semesterlecture.lecture_type2

                            semesterlecture.lecture_type2 = majorlecture.lecture_type
                            semesterlecture.recognized_major2 = majorlecture.major
                            semesterlecture.save()

                            if prev_lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
                                semester.major_requirement_credit -= lecture.credit
                                semester.save()
                            elif prev_lecture_type2 == SemesterLecture.MAJOR_ELECTIVE or prev_lecture_type2 == SemesterLecture.TEACHING:
                                semester.major_elective_credit -= lecture.credit
                                semester.save()
                            elif prev_lecture_type2 == SemesterLecture.GENERAL:
                                semester.general_credit -= lecture.credit
                                semester.save()
                            elif prev_lecture_type2 == SemesterLecture.GENERAL_ELECTIVE:
                                semester.general_elective_credit -= lecture.credit
                                semester.save()

                            if semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
                                semester.major_requirement_credit += lecture.credit
                                semester.save()
                            elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type2 == SemesterLecture.TEACHING:
                                semester.major_elective_credit += lecture.credit
                                semester.save()
                        else:
                            break

        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /plan/{plan_id}/major/
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def major(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = get_object_or_404(Plan, pk=pk)
        post_list = request.data.get("post_list", [])
        delete_list = request.data.get("delete_list", [])

        if len(list(UserMajor.objects.filter(user=user))) - len(delete_list) + len(post_list) <= 0:
            return Response({"error": "The number of majors cannot be zero or minus."}, status=status.HTTP_400_BAD_REQUEST)

        # update planmajor
        for major in delete_list:
            selected_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            selected_planmajor = PlanMajor.objects.get(plan=plan, major=selected_major)
            selected_planmajor.delete()

        for major in post_list:
            selected_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            PlanMajor.objects.create(plan=plan, major=selected_major)

        majors = Major.objects.filter(planmajor__plan=plan)
        majors = list(majors)
        if len(majors) == 1:
            if majors[0].major_type == Major.MAJOR:
                PlanMajor.objects.get(plan=plan, major=majors[0]).delete()
                new_type_major = Major.objects.get(major_name=majors[0].major_name, major_type=Major.SINGLE_MAJOR)
                PlanMajor.objects.create(plan=plan, major=new_type_major)
        else:
            for major in majors:
                if major.major_type == Major.SINGLE_MAJOR:
                    PlanMajor.objects.get(plan=plan, major=major).delete()
                    new_type_major = Major.objects.get(major_name=major.major_name, major_type=Major.MAJOR)
                    PlanMajor.objects.create(plan=plan, major=new_type_major)

        # update planrequirement
        for major in post_list:
            curr_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            requirements = Requirement.objects.filter(major=curr_major, start_year__lte=user.userprofile.entrance_year,
                                                      end_year__gte=user.userprofile.entrance_year)
            for requirement in list(requirements):
                PlanRequirement.objects.create(plan=plan, requirement=requirement, required_credit = requirement.required_credit)

        for major in delete_list:
            curr_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            requirements = Requirement.objects.filter(major=curr_major, start_year__lte=user.userprofile.entrance_year,
                                                      end_year__gte=user.userprofile.entrance_year)
            for requirement in list(requirements):
                selected_planrequirement = PlanRequirement.objects.get(plan=plan, requirement=requirement)
                selected_planrequirement.delete()

        self.calculate(request, pk)

        plan = get_object_or_404(Plan, pk=pk)
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /plan/{plan_id}/copy/
    @action(detail=True, methods=['POST'])
    @transaction.atomic
    def copy(self, request, pk=None):
        plan = get_object_or_404(Plan, pk=pk)
        new_plan = Plan.objects.create(user=plan.user,
                                       plan_name=plan.plan_name+'(복사본)',
                                       recent_scroll=0)

        majors = Major.objects.filter(planmajor__plan=plan)
        for major in list(majors):
            PlanMajor.objects.create(plan=new_plan, major=major)

        requirements = Requirement.objects.filter(planrequirement__plan=plan)
        for requirement in list(requirements):
            PlanRequirement.objects.create(plan=new_plan, requirement=requirement)

        semesters = Semester.objects.filter(plan=plan)
        for semester in list(semesters):
            new_semester = Semester.objects.create(plan=new_plan,
                                                   year=semester.year,
                                                   semester_type=semester.semester_type,
                                                   is_complete=semester.is_complete,
                                                   major_requirement_credit=semester.major_requirement_credit,
                                                   major_elective_credit=semester.major_elective_credit,
                                                   general_credit=semester.general_credit,
                                                   general_elective_credit=semester.general_elective_credit)

            semesterlectures = SemesterLecture.objects.filter(semester=semester)
            for sl in list(semesterlectures):
                SemesterLecture.objects.create(semester=new_semester,
                                               lecture=sl.lecture,
                                               lecture_type=sl.lecture_type,
                                               recognized_major1=sl.recognized_major1,
                                               lecture_type1=sl.lecture_type1,
                                               recognized_major2=sl.recognized_major2,
                                               lecture_type2=sl.lecture_type2,
                                               recent_sequence=sl.recent_sequence,
                                               is_modified=sl.is_modified)

        serializer = self.get_serializer(new_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
        if Semester.objects.filter(plan=plan, year=year, semester_type=semester_type).exists():
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

        plan = semester.plan
        year = data.get('year', None)
        semester_type = data.get('semester_type', None)
        is_complete = data.get('is_complete', None)

        if (is_complete is None) and (year is None) and (semester_type is None):
            return Response({"error": "body is empty"}, status=status.HTTP_403_FORBIDDEN)

        if (is_complete is None) == ((year is None) and (semester_type is None)):
            return Response({"error": "is_complete should be none"}, status=status.HTTP_403_FORBIDDEN)

        if is_complete is None:
            if Semester.objects.filter(plan=plan, year=year, semester_type=semester_type).exists():
                return Response({"error": "semester already_exist"}, status=status.HTTP_403_FORBIDDEN)

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

    # POST /lecture/
    @transaction.atomic
    def create(self, request): 
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        semester_id = request.data.get('semester_id')
        lecture_id_list = request.data.get('lecture_id')
        lecture_type_list = request.data.get('lecture_type')
        recognized_major_name_list = request.data.get('recognized_major_names')
        semester = Semester.objects.get(id=semester_id)
        plan = semester.plan

        if len(lecture_id_list) != len(set(lecture_id_list)):
            return Response({"error": "identical lectures in lecture_id_list"}, status=status.HTTP_400_BAD_REQUEST)

        lectures_in_plan = []
        sl_list = SemesterLecture.objects.filter(semester__plan=plan)
        for sl in sl_list:
            lectures_in_plan.append(sl.lecture.id)

        for lecture in lecture_id_list:
            if lecture in lectures_in_plan:
                return Response({"error": "identical lecture already exist"}, status=status.HTTP_400_BAD_REQUEST)

        lecture_in_semester = SemesterLecture.objects.filter(semester=semester)
        n_lectures = len(lecture_in_semester)
        for i in range(len(lecture_id_list)):
            lecture = Lecture.objects.get(id=lecture_id_list[i]) 
            lecture_type = lecture_type_list[i]
            recognized_major_name = recognized_major_name_list[i]

            if (lecture_type == Lecture.MAJOR_REQUIREMENT) \
                or (lecture_type == Lecture.MAJOR_ELECTIVE) \
                or (lecture_type == Lecture.TEACHING):

                if PlanMajor.objects.filter(plan=plan, major__major_name=recognized_major_name).exists():
                    recognized_major = Major.objects.get(planmajor__plan=plan, major_name=recognized_major_name)
                else:
                    recognized_major = Major.objects.get(id=Major.DEFAULT_MAJOR_ID)
                    lecture_type = Lecture.GENERAL_ELECTIVE
            else:
                recognized_major = Major.objects.get(id=Major.DEFAULT_MAJOR_ID)

            semlecture = SemesterLecture.objects.create(semester=semester,
                                                        lecture=lecture,
                                                        lecture_type=lecture_type,
                                                        recognized_major1=recognized_major,
                                                        lecture_type1=lecture_type,
                                                        recent_sequence=n_lectures+i)
            semlecture.save()

            if lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
                semester.major_requirement_credit += lecture.credit
                semester.save()
            elif lecture_type == SemesterLecture.MAJOR_ELECTIVE or lecture_type == SemesterLecture.TEACHING:
                semester.major_elective_credit += lecture.credit
                semester.save()
            elif lecture_type == SemesterLecture.GENERAL:
                semester.general_credit += lecture.credit
                semester.save()
            elif lecture_type == SemesterLecture.GENERAL_ELECTIVE:
                semester.general_elective_credit += lecture.credit
                semester.save()

        data = SemesterSerializer(semester).data
        return Response(data, status=status.HTTP_201_CREATED)
    
    # PUT /lecture/(int)/position/
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def position(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        lecture = get_object_or_404(Lecture, pk=pk)

        semester_from_id = request.data.get('semester_from_id')
        semester_to_id = request.data.get('semester_to_id')
        semester_from_list = request.data.get('semester_from')
        semester_to_list = request.data.get('semester_to')

        semester_from = Semester.objects.get(id=semester_from_id)

        semesterlecture = SemesterLecture.objects.get(semester_id=semester_from_id, lecture_id=lecture.id)

        print(semesterlecture.semester.major_elective_credit)
        subtract_credits(semesterlecture)
        print(semesterlecture.semester.major_elective_credit)
        semester_to = Semester.objects.get(id=semester_to_id)
        semesterlecture.semester = semester_to
        add_credits(semesterlecture)
        print(semesterlecture.semester.major_elective_credit)

        for i in range(len(semester_from_list)):
            semester_lecture = SemesterLecture.objects.get(semester_id=semester_from_id, lecture_id=semester_from_list[i])
            semester_lecture.recent_sequence = i
            semester_lecture.save()

        for i in range(len(semester_to_list)):
            semester_lecture = SemesterLecture.objects.get(semester_id=semester_to_id, lecture_id=semester_to_list[i])
            semester_lecture.recent_sequence = i
            semester_lecture.save()

        semester_to = Semester.objects.get(id=semester_to_id)
        semester_from = Semester.objects.get(id=semester_from_id)

        serializer = SemesterSerializer([semester_from, semester_to], many=True)
        data = serializer.data

        return Response(data, status=status.HTTP_200_OK)

    # PUT /lecture/{semesterlecture_id}/recognized_major/
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def recognized_major(self, request, pk=None):
        semesterlecture = self.get_object()
        lecture_type = request.data.get('lecture_type', None)

        subtract_credits(semesterlecture)

        # Case 1: lecture_type을 교양으로 변경
        if lecture_type == 'general':
            data = {
                "lecture_type": lecture_type,
                "recognized_major1": SemesterLecture.DEFAULT_MAJOR_ID,
                "recognized_major2": SemesterLecture.DEFAULT_MAJOR_ID,
                "lecture_type1": lecture_type,
                "lecture_type2": SemesterLecture.NONE,
                "is_modified": True
            }
            serializer = self.get_serializer(semesterlecture, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(semesterlecture, serializer.validated_data)
            serializer.save()

            add_credits(semesterlecture)

            return Response(serializer.data, status=status.HTTP_200_OK)

        # Case 2: 학과별 강의 구분을 recognized_major1,2와 lecture_type1,2을 이용해 입력
        elif lecture_type == 'major_requirement' or lecture_type == 'major_elective':
            recognized_major1 = Major.objects.get(major_name=request.data.get('recognized_major_name1'),
                                                  major_type=request.data.get('recognized_major_type1'))
            recognized_major2 = Major.objects.get(major_name=request.data.get('recognized_major_name2', Major.DEFAULT_MAJOR_NAME),
                                                  major_type=request.data.get('recognized_major_type2', Major.DEFAULT_MAJOR_TYPE))
            lecture_type1 = request.data.get('lecture_type1', SemesterLecture.NONE) 
            lecture_type2 = request.data.get('lecture_type2', SemesterLecture.NONE) 
            data = {
                "lecture_type": lecture_type, 
                "recognized_major1": recognized_major1.id,
                "recognized_major2": recognized_major2.id,
                "lecture_type1": lecture_type1, 
                "lecture_type2": lecture_type2,
                "is_modified": True
            }
            serializer = self.get_serializer(semesterlecture, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(semesterlecture, serializer.validated_data)
            serializer.save()

            add_credits(semesterlecture)

            return Response(serializer.data, status=status.HTTP_200_OK)

        # Case 3: lecture_type를 general_elective로 변경 
        elif lecture_type == 'general_elective':
            data = {
                "lecture_type": lecture_type,
                "recognized_major1": SemesterLecture.DEFAULT_MAJOR_ID,
                "recognized_major2": SemesterLecture.DEFAULT_MAJOR_ID,
                "lecture_type1": lecture_type,
                "lecture_type2": SemesterLecture.NONE,
                "is_modified": True
            }
            serializer = self.get_serializer(semesterlecture, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.update(semesterlecture, serializer.validated_data)
            serializer.save()

            add_credits(semesterlecture)

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"error": "wrong lecture_type"}, status=status.HTTP_400_BAD_REQUEST)

    # DEL /lecture/(int)/
    @transaction.atomic
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            semesterlecture = SemesterLecture.objects.get(pk=pk)
        except SemesterLecture.DoesNotExist:
            return Response({"error": "semesterlecture not_exist"}, status=status.HTTP_404_NOT_FOUND)
        subtract_credits(semesterlecture)
        semesterlecture.delete()
        return Response(status=status.HTTP_200_OK) 

    # GET /lecture/?search_type=(string)&search_keyword=(string)&major=(string)&credit=(string)
    @transaction.atomic
    def list(self, request):
        user = request.user

        # Pagination Parameter
        page = request.GET.get('page', '1')

        # Query Params
        search_type = request.query_params.get("search_type", None)
        if not search_type:
            return Response({ "error": "search_type missing" }, status=status.HTTP_400_BAD_REQUEST)

        # Case 1: major requirement or major elective
        if search_type == 'major_requirement' or search_type == 'major_elective':
            major_name = request.query_params.get("major_name", None)
            if major_name:
                lectures = Lecture.objects.filter(open_major=major_name, lecture_type=search_type)
                serializer = LectureSerializer(lectures, many=True)

                data = serializer.data
                for lecture in data:
                    lecture['lecture_type'] = search_type

                return Response(data, status=status.HTTP_200_OK)
            else: 
                return Response({"error": "major_name missing"}, status=status.HTTP_400_BAD_REQUEST)

        # Case 2: general
        elif search_type == 'general': 
            credit = request.query_params.get("credit", None)
            search_keyword = request.query_params.get("search_keyword", None)
            if credit and search_keyword:
                lectures = Lecture.objects.filter(credit=credit, lecture_name__icontains=search_keyword) 
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "credit or search keyword missing"}, status=status.HTTP_400_BAD_REQUEST) 

        # Case 3: keyword
        else:
            search_keyword = request.query_params.get("search_keyword", None)
            if search_keyword:
                lectures = Lecture.objects.filter(lecture_name__icontains=search_keyword)
                lectures = Paginator(lectures, 20).get_page(page)
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "search_keyword missing"}, status=status.HTTP_400_BAD_REQUEST)

# 공용 함수 모음
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
    switcher = {
        SemesterLecture.MAJOR_REQUIREMENT : 1,
        SemesterLecture.MAJOR_ELECTIVE : 2,
        SemesterLecture.TEACHING : 3,
        SemesterLecture.GENERAL : 4,
        SemesterLecture.GENERAL_ELECTIVE : 5
    }
    return switcher.get(semesterlecture, -1) # -1은 에러

def add_credits(semesterlecture):
    semester = semesterlecture.semester

    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.lecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.lecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit += semesterlecture.lecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit += semesterlecture.lecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.lecture.credit

    semester.save()

def subtract_credits(semesterlecture):
    semester = semesterlecture.semester

    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.lecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.lecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit -= semesterlecture.lecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit -= semesterlecture.lecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit -= semesterlecture.lecture.credit

    semester.save()