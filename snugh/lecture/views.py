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

    # POST /plan
    @transaction.atomic
    def create(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data
        plan_name = data.get("plan_name")
        majors = data.get("majors")

        # error case 1
        if not majors:
            return Response({"error": "majors missing"}, status=status.HTTP_400_BAD_REQUEST)
        for major in majors:
                if not Major.objects.filter(major_name=major['major_name'], major_type=major['major_type']).exists():
                    return Response({"error": "major not_exist"}, status=status.HTTP_404_NOT_FOUND)

        # plan
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
        if len(majors) == 1 and majors[0]['major_type'] == Major.MAJOR:
            searched_major = Major.objects.get(major_name=majors[0]['major_name'], major_type=Major.SINGLE_MAJOR)
            requirements = Requirement.objects.filter(major=searched_major,
                                                      start_year__lte=user.userprofile.entrance_year,
                                                      end_year__gte=user.userprofile.entrance_year)
            for requirement in requirements:
                PlanRequirement.objects.create(plan=plan, requirement=requirement, required_credit=requirement.required_credit)
        else:
            for major in majors:
                searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
                requirements = Requirement.objects.filter(major=searched_major,
                                                          start_year__lte=user.userprofile.entrance_year,
                                                          end_year__gte=user.userprofile.entrance_year)
                for requirement in requirements:
                    PlanRequirement.objects.create(plan=plan, requirement=requirement, required_credit=requirement.required_credit)

        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /plan/:planId
    @transaction.atomic
    def update(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data
        plan = get_object_or_404(Plan, pk=pk)
        serializer = self.get_serializer(plan, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(plan, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /plan/:planId
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = get_object_or_404(Plan, pk=pk)
        plan.delete()
        return Response(status=status.HTTP_200_OK)

    # GET /plan/:planId
    def retrieve(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = get_object_or_404(Plan, pk=pk)
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /plan
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plans = Plan.objects.filter(user=user)
        return Response(self.get_serializer(plans, many=True).data, status=status.HTTP_200_OK)

    # 강의구분 자동계산
    # PUT /plan/:planId/calculate
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def calculate(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = get_object_or_404(Plan, pk=pk)

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

    # PUT /plan/:planId/major
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def major(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = get_object_or_404(Plan, pk=pk)
        post_list = request.data.get("post_list", [])
        delete_list = request.data.get("delete_list", [])

        if len(list(PlanMajor.objects.filter(plan=plan))) - len(delete_list) + len(post_list) <= 0:
            return Response({"error": "The number of majors cannot be zero or minus."}, status=status.HTTP_400_BAD_REQUEST)

        # update planmajor
        for major in delete_list:
            selected_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            PlanMajor.objects.get(plan=plan, major=selected_major).delete()

        for major in post_list:
            selected_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            PlanMajor.objects.create(plan=plan, major=selected_major)

        # update major type
        majors = list(Major.objects.filter(planmajor__plan=plan))

        if len(majors) == 1:
            major = majors[0]
            if major.major_type == Major.MAJOR:
                PlanMajor.objects.get(plan=plan, major=major).delete()
                new_type_major = Major.objects.get(major_name=major.major_name, major_type=Major.SINGLE_MAJOR)
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
            requirements = Requirement.objects.filter(major=curr_major,
                                                      start_year__lte=user.userprofile.entrance_year,
                                                      end_year__gte=user.userprofile.entrance_year)
            for requirement in list(requirements):
                PlanRequirement.objects.create(plan=plan, requirement=requirement, required_credit=requirement.required_credit)

        for major in delete_list:
            curr_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            requirements = Requirement.objects.filter(major=curr_major,
                                                      start_year__lte=user.userprofile.entrance_year,
                                                      end_year__gte=user.userprofile.entrance_year)
            for requirement in list(requirements):
                PlanRequirement.objects.get(plan=plan, requirement=requirement).delete()

        self.calculate(request, pk=pk)

        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /plan/:planId/copy
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
            PlanRequirement.objects.create(plan=new_plan, requirement=requirement, required_credit=requirement.required_credit)

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
                                               credit=sl.credit,
                                               recent_sequence=sl.recent_sequence,
                                               is_modified=sl.is_modified)

        serializer = self.get_serializer(new_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SemesterViewSet(viewsets.GenericViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer

    # POST /semester
    @transaction.atomic
    def create(self, request): 
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        plan = request.data.get('plan')
        year = request.data.get('year')
        semester_type = request.data.get('semester_type')

        if not plan:
            return Response({"error": "plan missing"}, status=status.HTTP_400_BAD_REQUEST)
        if not year:
            return Response({"error": "year missing"}, status=status.HTTP_400_BAD_REQUEST)
        if not semester_type:
            return Response({"error": "semester_type missing"}, status=status.HTTP_400_BAD_REQUEST)
        if Semester.objects.filter(plan=plan, year=year, semester_type=semester_type).exists():
            return Response({"error": "semester already_exist"}, status=status.HTTP_403_FORBIDDEN)
        
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /semester/:semesterId
    @transaction.atomic
    def update(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data

        semester = self.get_object()
        plan = semester.plan
        year = data.get('year')
        semester_type = data.get('semester_type')
        is_complete = data.get('is_complete')

        if (not is_complete) and (not year) and (not semester_type):
            return Response({"error": "body is empty"}, status=status.HTTP_403_FORBIDDEN)

        if (not is_complete) == ((not year) and (not semester_type)):
            return Response({"error": "is_complete should be none"}, status=status.HTTP_403_FORBIDDEN)

        if not is_complete:
            if Semester.objects.filter(plan=plan, year=year, semester_type=semester_type).exists():
                return Response({"error": "semester already_exist"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(semester, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semester, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /semester/:semesterId
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        semester = self.get_object()
        plan = semester.plan
        semester.delete()
        # TODO: update plan info when delete semester
        # update_plan_info(plan=plan)
        return Response(status=status.HTTP_200_OK)
    
    # GET /semester/:semesterId
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
                                                        credit=lecture.credit,
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
    
    # PUT /lecture/:lectureId/position
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

        subtract_credits(semesterlecture)
        semester_to = Semester.objects.get(id=semester_to_id)
        semesterlecture.semester = semester_to
        add_credits(semesterlecture)
        semesterlecture.save()

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

    # PUT /lecture/:semesterLectureId/credit
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def credit(self, request, pk=None):
        semesterlecture = self.get_object()
        credit = request.data.get('credit', 0)

        if credit != 1 and credit != 2 and credit !=3 and credit !=4:
            return Response({"error": "enter valid credit"}, status=status.HTTP_400_BAD_REQUEST)

        if credit == semesterlecture.credit:
            return Response(SemesterLectureSerializer(semesterlecture).data, status=status.HTTP_200_OK)

        # create creditchangehistory
        # lecture_type = general or general_elective
        if semesterlecture.lecture_type == SemesterLecture.GENERAL or semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
            creditchangehistory = CreditChangeHistory.objects.filter(major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                                                                    lecture=semesterlecture.lecture,
                                                                    entrance_year=user.userprofile.entrance_year,
                                                                    past_credit=semesterlecture.credit,
                                                                    curr_credit=credit)
            if creditchangehistory.count() == 0:
                CreditChangeHistory.objects.create(major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                                                    lecture=semesterlecture.lecture,
                                                    entrance_year=user.userprofile.entrance_year,
                                                    past_credit=semesterlecture.credit,
                                                    curr_credit=credit)
            else:
                creditchangehistory = CreditChangeHistory.objects.get(major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                                                                    lecture=semesterlecture.lecture,
                                                                    entrance_year=user.userprofile.entrance_year,
                                                                    past_credit=semesterlecture.credit,
                                                                    curr_credit=credit)
                creditchangehistory.change_count += 1
                creditchangehistory.save()
        # lecture_type = major_requirement or major_elective
        else:
            recognized_majors = [semesterlecture.recognized_major1, semesterlecture.recognized_major2]
            for i in range(2):
                if recognized_majors[i].id != Major.DEFAULT_MAJOR_ID:
                    creditchangehistory = CreditChangeHistory.objects.filter(major=recognized_majors[i],
                                                                            lecture=semesterlecture.lecture,
                                                                            entrance_year=user.userprofile.entrance_year,
                                                                            past_credit=semesterlecture.credit,
                                                                            curr_credit=credit)
                    if creditchangehistory.count() == 0:
                        CreditChangeHistory.objects.create(major=recognized_majors[i],
                                                           lecture=semesterlecture.lecture,
                                                           entrance_year=user.userprofile.entrance_year,
                                                           past_credit=semesterlecture.credit,
                                                           curr_credit=credit)
                    else:
                        creditchangehistory = CreditChangeHistory.objects.get(major=recognized_majors[i],
                                                                            lecture=semesterlecture.lecture,
                                                                            entrance_year=user.userprofile.entrance_year,
                                                                            past_credit=semesterlecture.credit,
                                                                            curr_credit=credit)
                        creditchangehistory.change_count += 1
                        creditchangehistory.save()

        # update semesterlecture
        subtract_credits(semesterlecture)

        semesterlecture.credit = credit
        semesterlecture.is_modified = True
        semesterlecture.save()

        add_credits(semesterlecture)

        data = SemesterLectureSerializer(semesterlecture).data
        return Response(data, status=status.HTTP_200_OK)


    # PUT /lecture/:semesterLectureId/recognized_major
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def recognized_major(self, request, pk=None):
        semesterlecture = self.get_object()
        lecture_type = request.data.get('lecture_type', None)
        user = request.user

        subtract_credits(semesterlecture)

        if lecture_type == 'general' or lecture_type == 'general_elective':
            # (other) -> general or general_elective 일때: major = none(default)
            past_recognized_majors = [semesterlecture.recognized_major1, semesterlecture.recognized_major2]
            past_lecture_types = [semesterlecture.lecture_type1, semesterlecture.lecture_type2]

            # Create lecturetypechangehistory: major = default_major_id, curr_lecture_type = general or general_elective
            # lecturetypechangehistory의 major가 default major 인 유일한 경우 --??
            # 일선으로 바꿀 때는 저장 안함.
            if semesterlecture.lecture_type != lecture_type and lecture_type != SemesterLecture.GENERAL_ELECTIVE:
                lecturetypechangehistory = LectureTypeChangeHistory.objects.filter(major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                                                                        lecture=semesterlecture.lecture,
                                                                        entrance_year=user.userprofile.entrance_year,
                                                                        past_lecture_type=semesterlecture.NONE,
                                                                        curr_lecture_type=lecture_type)
                if lecturetypechangehistory.count() == 0:
                    LectureTypeChangeHistory.objects.create(major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                                                        lecture=semesterlecture.lecture,
                                                        entrance_year=user.userprofile.entrance_year,
                                                        past_lecture_type=semesterlecture.NONE,
                                                        curr_lecture_type=lecture_type)
                else:
                    lecturetypechangehistory = LectureTypeChangeHistory.objects.get(
                        major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                        lecture=semesterlecture.lecture,
                        entrance_year=user.userprofile.entrance_year,
                        past_lecture_type=semesterlecture.NONE,
                        curr_lecture_type=lecture_type)
                    lecturetypechangehistory.change_count += 1
                    lecturetypechangehistory.save()

            # Create major = past_major_id, curr_lecture_type = none
            for i in range(2):
                past_recognized_major = past_recognized_majors[i]
                past_lecture_type = past_lecture_types[i]

                if past_recognized_major.id != SemesterLecture.DEFAULT_MAJOR_ID:
                    lecturetypechangehistory = LectureTypeChangeHistory.objects.filter(major=past_recognized_major,
                                                                               lecture=semesterlecture.lecture,
                                                                               entrance_year=user.userprofile.entrance_year,
                                                                               past_lecture_type=past_lecture_type,
                                                                               curr_lecture_type=LectureTypeChangeHistory.NONE)
                    if lecturetypechangehistory.count() == 0:
                        LectureTypeChangeHistory.objects.create(major=past_recognized_major,
                                                            lecture=semesterlecture.lecture,
                                                            entrance_year=user.userprofile.entrance_year,
                                                            past_lecture_type=past_lecture_type,
                                                            curr_lecture_type=LectureTypeChangeHistory.NONE)
                    else:
                        lecturetypechangehistory = LectureTypeChangeHistory.objects.get(major=past_recognized_major,
                                                                                   lecture=semesterlecture.lecture,
                                                                                   entrance_year=user.userprofile.entrance_year,
                                                                                   past_lecture_type=past_lecture_type,
                                                                                   curr_lecture_type=LectureTypeChangeHistory.NONE)
                        lecturetypechangehistory.change_count += 1
                        lecturetypechangehistory.save()

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

            # 새롭게 만들어진 lecturehistory의 major 는 default major 가 될 수 없음
            past_recognized_major_check = [False, False]
            curr_recognized_major_check = [False, False]
            past_recognized_majors = [semesterlecture.recognized_major1, semesterlecture.recognized_major2]
            curr_recognized_majors = [recognized_major1, recognized_major2]
            past_lecture_types = [semesterlecture.lecture_type1, semesterlecture.lecture_type2]
            curr_lecture_types = [lecture_type1, lecture_type2]

            for i in range(2):
                past_recognized_major = past_recognized_majors[i]
                for j in range(2):
                    if curr_recognized_major_check[j] == False:
                        curr_recognized_major = curr_recognized_majors[j]
                        if past_recognized_major.id == curr_recognized_major.id:
                            curr_recognized_major_check[j] = True
                            past_recognized_major_check[i] = True
                            # Create lecturetypechangehistory: major = past_major = curr_major
                            if past_lecture_types[i] != curr_lecture_types[j] and past_recognized_major.id != Major.DEFAULT_MAJOR_ID:
                                lecturetypechangehistory = LectureTypeChangeHistory.objects.filter(major=past_recognized_major,
                                                                                        lecture=semesterlecture.lecture,
                                                                                        entrance_year=user.userprofile.entrance_year,
                                                                                        past_lecture_type=past_lecture_types[i],
                                                                                        curr_lecture_type=curr_lecture_types[j])
                                if lecturetypechangehistory.count() == 0:
                                    LectureTypeChangeHistory.objects.create(major=past_recognized_major,
                                                                        lecture=semesterlecture.lecture,
                                                                        entrance_year=user.userprofile.entrance_year,
                                                                        past_lecture_type=past_lecture_types[i],
                                                                        curr_lecture_type=curr_lecture_types[j])
                                else:
                                    lecturetypechangehistory = LectureTypeChangeHistory.objects.get(
                                        major=past_recognized_major,
                                        lecture=semesterlecture.lecture,
                                        entrance_year=user.userprofile.entrance_year,
                                        past_lecture_type=past_lecture_types[i],
                                        curr_lecture_type=curr_lecture_types[j])
                                    lecturetypechangehistory.change_count += 1
                                    lecturetypechangehistory.save()

                # 단일인정, none -> 복수인정, 새로운 과에서 복수인정, 복수인정 -> 단일인정, none
                # past_recognized major에서 더이상 major_elective, major_requirement 아님
                if past_recognized_major_check[i] == False and past_lecture_types[i] != SemesterLecture.NONE and past_lecture_types[i] != SemesterLecture.GENERAL_ELECTIVE:
                    # Create lecturetypechangehistory: major = past_major, curr_lecture_type = none
                    lecturetypechangehistory = LectureTypeChangeHistory.objects.filter(major=past_recognized_major,
                                                                               lecture=semesterlecture.lecture,
                                                                               entrance_year=user.userprofile.entrance_year,
                                                                               past_lecture_type=past_lecture_types[i],
                                                                               curr_lecture_type=LectureTypeChangeHistory.NONE)
                    if lecturetypechangehistory.count() == 0:
                        LectureTypeChangeHistory.objects.create(major=past_recognized_major,
                                                            lecture=semesterlecture.lecture,
                                                            entrance_year=user.userprofile.entrance_year,
                                                            past_lecture_type=past_lecture_types[i],
                                                            curr_lecture_type=LectureTypeChangeHistory.NONE)
                    else:
                        lecturetypechangehistory = LectureTypeChangeHistory.objects.get(major=past_recognized_major,
                                                                                   lecture=semesterlecture.lecture,
                                                                                   entrance_year=user.userprofile.entrance_year,
                                                                                   past_lecture_type=past_lecture_types[
                                                                                       i],
                                                                                   curr_lecture_type=LectureTypeChangeHistory.NONE)
                        lecturetypechangehistory.change_count += 1
                        lecturetypechangehistory.save()
            # curr_major에서 새롭게 major_elective, major_requirement 인
            for i in range(2):
                # Create lecturetypechangehistory: major = curr_major, curr_lecture_type = major_elective or major_requirement
                if curr_recognized_major_check[i] == False and curr_lecture_types[i] != SemesterLecture.NONE and curr_lecture_types[i] != SemesterLecture.GENERAL_ELECTIVE:
                    lecturetypechangehistory = LectureTypeChangeHistory.objects.filter(major=curr_recognized_majors[i],
                                                                               lecture=semesterlecture.lecture,
                                                                               entrance_year=user.userprofile.entrance_year,
                                                                               past_lecture_type=LectureTypeChangeHistory.NONE,
                                                                               curr_lecture_type=curr_lecture_types[i])
                    if lecturetypechangehistory.count() == 0:
                        LectureTypeChangeHistory.objects.create(major=curr_recognized_majors[i],
                                                           lecture=semesterlecture.lecture,
                                                           entrance_year=user.userprofile.entrance_year,
                                                           past_lecture_type=LectureTypeChangeHistory.NONE,
                                                           curr_lecture_type=curr_lecture_types[i])
                    else:
                        lecturetypechangehistory = LectureTypeChangeHistory.objects.get(major=curr_recognized_majors[i],
                                                                                   lecture=semesterlecture.lecture,
                                                                                   entrance_year=user.userprofile.entrance_year,
                                                                                   past_lecture_type=LectureTypeChangeHistory.NONE,
                                                                                   curr_lecture_type=curr_lecture_types[
                                                                                       i])
                        lecturetypechangehistory.change_count += 1
                        lecturetypechangehistory.save()

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

    # DEL /lecture/:semlectureId
    @transaction.atomic
    def destroy(self, request, pk=None):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        semesterlecture = get_object_or_404(SemesterLecture, pk=pk)
        subtract_credits(semesterlecture)
        semesterlecture.delete()
        return Response(status=status.HTTP_200_OK) 

    # GET /lecture/?search_type=(string)&search_keyword=(string)&major=(string)&credit=(string)
    # TODO: recent_open_year 최근순 정렬, filter
    def list(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Pagination Parameter
        page = request.GET.get('page', '1')

        # Query Params
        search_type = request.query_params.get("search_type")
        if not search_type:
            return Response({ "error": "search_type missing" }, status=status.HTTP_400_BAD_REQUEST)

        # Case 1: major requirement or major elective
        if search_type == 'major_requirement' or search_type == 'major_elective':
            major_name = request.query_params.get("major_name")
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
            credit = request.query_params.get("credit")
            search_keyword = request.query_params.get("search_keyword")
            if credit and search_keyword:
                lectures = Lecture.objects.filter(credit=credit, lecture_name__search=search_keyword)
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "credit or search keyword missing"}, status=status.HTTP_400_BAD_REQUEST) 

        # Case 3: keyword
        else:
            search_keyword = request.query_params.get("search_keyword")
            if search_keyword:
                lectures = Lecture.objects.filter(lecture_name__search=search_keyword)
                lectures = Paginator(lectures, 20).get_page(page)
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "search_keyword missing"}, status=status.HTTP_400_BAD_REQUEST)


# Common Functions
def add_credits(semesterlecture):
    semester = semesterlecture.semester

    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit

    semester.save()

def subtract_credits(semesterlecture):
    semester = semesterlecture.semester

    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit -= semesterlecture.credit

    semester.save()

# Deprecated Common Functions
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
    return switcher.get(lecture_type, -1) # -1 is error

def lecture_type_to_int(semesterlecture):
    switcher = {
        SemesterLecture.MAJOR_REQUIREMENT : 1,
        SemesterLecture.MAJOR_ELECTIVE : 2,
        SemesterLecture.TEACHING : 3,
        SemesterLecture.GENERAL : 4,
        SemesterLecture.GENERAL_ELECTIVE : 5
    }
    return switcher.get(semesterlecture, -1) # -1 is error

