from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db.models import Case, When
from django.db import transaction
from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from lecture.models import * 
from lecture.serializers import *
from user.models import *
from requirement.models import *
from django.core.paginator import Paginator
from django.db.models.functions import Length
from django.db.models import F


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

        # order majors(기준: 졸업요구 전공학점 높은 순서)
        majors = Major.objects.filter(planmajor__plan=plan)\
            .annotate(custom_order=Case(When(major_type=Major.SINGLE_MAJOR, then=models.Value(0)),
                                        When(major_type=Major.MAJOR, then=models.Value(1)),
                                        When(major_type=Major.GRADUATE_MAJOR, then=models.Value(2)),
                                        When(major_type=Major.INTERDISCIPLINARY_MAJOR, then=models.Value(3)),
                                        When(major_type=Major.INTERDISCIPLINARY_MAJOR_FOR_TEACHER, then=models.Value(4)),
                                        When(major_type=Major.DOUBLE_MAJOR, then=models.Value(5)),
                                        When(major_type=Major.INTERDISCIPLINARY, then=models.Value(6)),
                                        When(major_type=Major.MINOR, then=models.Value(7)),
                                        When(major_type=Major.INTERDISCIPLINARY_PROGRAM, then=models.Value(8)),
                                        default=models.Value(9),
                                        output_field=models.IntegerField(), ))\
            .order_by('custom_order')

        for semesterlecture in semesterlectures:
            # create variable tmp_majors for use only in loop(1 semesterlecture)
            tmp_majors = majors
            # exclude is_modified = True
            if not semesterlecture.is_modified:
                # subtract credits
                subtract_credits(semesterlecture)

                semester = semesterlecture.semester
                lecture = semesterlecture.lecture

                # calculate lecture_type for each semesterlecture
                # search majorlecture by entrance_year
                if semesterlecture.lecture_type != SemesterLecture.GENERAL:
                    major_count = 0
                    for major in tmp_majors:
                        if major_count > 1:
                            break

                        candidate_majorlectures = MajorLecture.objects.filter(lecture=lecture, major=major,
                                                                              start_year__lte=user.userprofile.entrance_year,
                                                                              end_year__gte=user.userprofile.entrance_year)\
                            .exclude(lecture_type=MajorLecture.GENERAL).exclude(lecture_type = MajorLecture.GENERAL_ELECTIVE)\
                            .order_by('-lecture_type')

                        if candidate_majorlectures.count() !=0:
                            if major_count == 0:
                                semesterlecture.lecture_type = candidate_majorlectures.first().lecture_type
                                semesterlecture.lecture_type1 = candidate_majorlectures.first().lecture_type
                                semesterlecture.recognized_major1 = major
                                semesterlecture.save()
                            elif major_count == 1:
                                semesterlecture.lecture_type2 = candidate_majorlectures.first().lecture_type
                                semesterlecture.recognized_major2 = major
                                semesterlecture.save()
                            major_count += 1

                    if major_count != 2:
                        if major_count == 1:
                            tmp_majors = tmp_majors.exclude(id=semesterlecture.recognized_major1.id)
                        # search majorlecture by semester.year
                        for major in tmp_majors:
                            if major_count > 1:
                                break

                            candidate_majorlectures = MajorLecture.objects.filter(lecture=lecture, major=major,
                                                                                  start_year__lte=semester.year,
                                                                                  end_year__gte=semester.year)\
                                .exclude(lecture_type=MajorLecture.GENERAL).exclude(lecture_type = MajorLecture.GENERAL_ELECTIVE)\
                                .order_by('-lecture_type')
                            if candidate_majorlectures.count() != 0:
                                if major_count == 0:
                                    semesterlecture.lecture_type = candidate_majorlectures.first().lecture_type
                                    semesterlecture.lecture_type1 = candidate_majorlectures.first().lecture_type
                                    semesterlecture.recognized_major1 = major
                                    semesterlecture.save()
                                elif major_count == 1:
                                    semesterlecture.lecture_type2 = candidate_majorlectures.first().lecture_type
                                    semesterlecture.recognized_major2 = major
                                    semesterlecture.save()
                                major_count += 1

                    if major_count == 1:
                        semesterlecture.lecture_type2 = SemesterLecture.NONE
                        semesterlecture.recognized_major2 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                        semesterlecture.save()
                    elif major_count == 0:
                        semesterlecture.lecture_type = SemesterLecture.GENERAL_ELECTIVE
                        semesterlecture.lecture_type1 = SemesterLecture.GENERAL_ELECTIVE
                        semesterlecture.recognized_major1 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                        semesterlecture.lecture_type2 = SemesterLecture.NONE
                        semesterlecture.recognized_major2 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                        semesterlecture.save()

                # calculate credit for each semesterlecture

                # lecturecredits = LectureCredit.objects.filter(lecture=lecture,
                #                                               start_year__lte=user.userprofile.entrance_year,
                #                                               end_year__gte=user.userprofile.entrance_year)
                # if lecturecredits.count() == 0:
                #     lecturecredits = LectureCredit.objects.filter(lecture=lecture,
                #                                                   start_year__lte=semester.year,
                #                                                   end_year__gte=semester.year)
                lecturecredits = LectureCredit.objects.filter(lecture=lecture,
                                                              start_year__lte=semester.year,
                                                              end_year__gte=semester.year)

                if lecturecredits.count() > 0:
                    semesterlecture.credit = lecturecredits.first().credit
                    semesterlecture.save()

                 # add credits
                add_credits(semesterlecture)

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

        # error case 1
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
            curr_major_type = major['major_type']
            if len(majors) == 1:
                curr_major_type = Major.SINGLE_MAJOR
            curr_major = Major.objects.get(major_name=major['major_name'], major_type= curr_major_type)
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
                                       plan_name=plan.plan_name+' (복사본)',
                                       recent_scroll=0)

        majors = Major.objects.filter(planmajor__plan=plan)
        for major in list(majors):
            PlanMajor.objects.create(plan=new_plan, major=major)

        planrequirements = PlanRequirement.objects.filter(plan=plan)
        for planrequirement in list(planrequirements):
            PlanRequirement.objects.create(plan=new_plan, requirement=planrequirement.requirement, required_credit=planrequirement.required_credit)

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

        semlectures = []
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
            semlectures.append(semlecture)

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

        calculate_by_lecture(user, plan, semlectures)
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
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        semesterlecture = self.get_object()
        credit = request.data.get('credit', 0)
        year_taken = semesterlecture.semester.year

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
                                                                    year_taken = year_taken,
                                                                    past_credit=semesterlecture.credit,
                                                                    curr_credit=credit)
            if creditchangehistory.count() == 0:
                CreditChangeHistory.objects.create(major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                                                    lecture=semesterlecture.lecture,
                                                    entrance_year=user.userprofile.entrance_year,
                                                    year_taken=year_taken,
                                                    past_credit=semesterlecture.credit,
                                                    curr_credit=credit)
            else:
                creditchangehistory = CreditChangeHistory.objects.get(major=Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID),
                                                                    lecture=semesterlecture.lecture,
                                                                    year_taken=year_taken,
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
                                                                            year_taken=year_taken,
                                                                            past_credit=semesterlecture.credit,
                                                                            curr_credit=credit)
                    if creditchangehistory.count() == 0:
                        CreditChangeHistory.objects.create(major=recognized_majors[i],
                                                           lecture=semesterlecture.lecture,
                                                           entrance_year=user.userprofile.entrance_year,
                                                           year_taken=year_taken,
                                                           past_credit=semesterlecture.credit,
                                                           curr_credit=credit)
                    else:
                        creditchangehistory = CreditChangeHistory.objects.get(major=recognized_majors[i],
                                                                            lecture=semesterlecture.lecture,
                                                                            entrance_year=user.userprofile.entrance_year,
                                                                            year_taken=year_taken,
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
    # TODO: n-gram 서치 고도화
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

        # search_year = request.query_params.get("search_year")
        # if not search_year:
        #     return Response({"error": "search_year missing"}, status=status.HTTP_400_BAD_REQUEST)
        #
        # plan_id = request.query_params.get("plan_id")
        # if not plan_id:
        #     return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)

#        existing_lectures = Lecture.objects.filter(semesterlecture__semester__plan = Plan.objects.get(id=plan_id)).values_list('id', flat=True)

        # Case 1: major requirement or major elective
        if search_type == 'major_requirement' or search_type == 'major_elective':
            major_name = request.query_params.get("major_name")
            if major_name:
                # 시연에서만
                search_year = 2019

                if int(search_year) < Lecture.UPDATED_YEAR:
                    year_standard = search_year
                else:
                    year_standard = Lecture.UPDATED_YEAR-2

                lectures = Lecture.objects.filter(open_major=major_name, lecture_type=search_type,
                                                  recent_open_year__gte = year_standard) \
                    .order_by('lecture_name', 'recent_open_year')
                # lectures = Lecture.objects.filter(open_major=major_name, lecture_type=search_type, recent_open_year__gte=user.userprofile.entrance_year)\
                #     .exclude(id__in=existing_lectures).order_by('lecture_name', 'recent_open_year')
                if DepartmentEquivalent.objects.filter(major_name=major_name).count() != 0:
                    department_name = DepartmentEquivalent.objects.get(major_name=major_name).department_name
                    # TODO: |= inefficient
                    lectures |= (Lecture.objects.filter(open_department=department_name, lecture_type=search_type,
                                                  recent_open_year__gte = year_standard)
                                    .order_by('lecture_name', 'recent_open_year'))

                if MajorEquivalent.objects.filter(major_name=major_name).count() != 0:
                    equivalent_majors = MajorEquivalent.objects.filter(major_name=major_name)
                    for equivalent_major in equivalent_majors:
                        lectures |= (Lecture.objects.filter(open_major=equivalent_major.equivalent_major_name, lecture_type=search_type,
                                                  recent_open_year__gte = year_standard)
                                        .order_by('lecture_name', 'recent_open_year'))

                serializer = LectureSerializer(lectures, many=True)

                data = serializer.data
                for lecture in data:
                    lecture['lecture_type'] = search_type

                return Response(data, status=status.HTTP_200_OK)
            else: 
                return Response({"error": "major_name missing"}, status=status.HTTP_400_BAD_REQUEST)

        # Case 2: general -- deprecated
        elif search_type == 'general': 
            credit = request.query_params.get("credit")
            search_keyword = request.query_params.get("search_keyword")
            if credit and search_keyword:
                lectures = Lecture.objects.filter(credit=credit, lecture_name__search=search_keyword).order_by('-recent_open_year')
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "credit or search keyword missing"}, status=status.HTTP_400_BAD_REQUEST) 

        # Case 3: keyword
        else:
            # 시연에서만
            search_year = request.query_params.get("search_year")
            if not search_year:
                return Response({"error": "search_year missing"}, status=status.HTTP_400_BAD_REQUEST)

            plan_id = request.query_params.get("plan_id")
            if not plan_id:
                return Response({"error": "plan_id missing"}, status=status.HTTP_400_BAD_REQUEST)

            search_keyword = request.query_params.get("search_keyword")
            if search_keyword:
                # past lectures
                if int(search_year) < Lecture.UPDATED_YEAR:
                    # .exclude(id__in=existing_lectures) \
                    lectures = Lecture.objects.search(search_keyword).filter(recent_open_year__gte = search_year)\
                        .annotate(first_letter=Case(When(lecture_name__startswith=search_keyword[0], then=models.Value(0)),
                                                default=models.Value(1),
                                                output_field=models.IntegerField(),))\
                        .annotate(icontains_priority=Case(When(lecture_name__icontains=search_keyword, then=models.Value(0)),
                                                default=models.Value(1),
                                                output_field=models.IntegerField(),))\
                        .annotate(priority = F('first_letter')+F('icontains_priority'))\
                        .annotate(match_rate=Length('lecture_name'))\
                        .order_by('priority', 'match_rate', 'recent_open_year', 'lecture_name')
                # future lectures
                else:
                    # .exclude(id__in=existing_lectures) \
                    lectures = Lecture.objects.search(search_keyword).filter(recent_open_year__gte=Lecture.UPDATED_YEAR-2) \
                        .annotate(first_letter=Case(When(lecture_name__startswith=search_keyword[0], then=models.Value(0)),
                                          default=models.Value(1),
                                          output_field=models.IntegerField(), )) \
                        .annotate(icontains_priority=Case(When(lecture_name__icontains=search_keyword, then=models.Value(0)),
                                                default=models.Value(1),
                                                output_field=models.IntegerField(), )) \
                        .annotate(priority=F('first_letter') + F('icontains_priority')) \
                        .annotate(match_rate=Length('lecture_name'))\
                        .order_by('priority', 'match_rate', '-recent_open_year', 'lecture_name')
                lectures = Paginator(lectures, 20).get_page(page)
                serializer = LectureSerializer(lectures, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response([], status=status.HTTP_200_OK)

    # Data Generation
    # POST /lecture/generate_lecturecredit/
    @action(methods=['POST'], detail=False)
    @transaction.atomic
    def generate_lecturecredit(self, request):
        lectures = Lecture.objects.all()
        id_cnt = 0 # 이전 item의 id
        for lecture in lectures:
            lecture_code = lecture.lecture_code
            lecturecredits = LectureTmp.objects.filter(lecture_code=lecture_code).order_by('id')
            if lecturecredits.count() == 0:
                return Response({"error": "lecture missing"}, status=status.HTTP_400_BAD_REQUEST)
            elif lecturecredits.count() == 1:
                LectureCredit.objects.create(lecture=lecture,
                                             credit=lecturecredits.first().credit,
                                             start_year=lecturecredits.first().open_year,
                                             end_year = 10000)
                id_cnt+=1;
            else:
                cnt = 0
                for lecturecredit in lecturecredits:
                    LectureCredit.objects.create(lecture=lecture,
                                                 credit=lecturecredit.credit,
                                                 start_year=lecturecredit.open_year,
                                                 end_year=10000)
                    if cnt !=0:
                        prev_lecturecredit = LectureCredit.objects.get(id=id_cnt)
                        prev_lecturecredit.end_year = lecturecredit.open_year -1
                        prev_lecturecredit.save()
                    cnt +=1
                    id_cnt+=1
        return Response(status=status.HTTP_200_OK)

    # POST /lecture/combine_majorlecture/
    # 수집된 데이터와 수강신청 사이트의 데이터 합치기(수강신청 사이트 데이터에 없는 강의만 추가)
    @action(methods=['POST'], detail=False)
    @transaction.atomic
    def combine_majorlecture(self, request):
        cnt_created=0
        majors = Major.objects.exclude(major_type = Major.SINGLE_MAJOR).exclude(major_type=Major.DOUBLE_MAJOR).exclude(major_type=Major.MINOR)
        for major in majors:
            majorlectures_auto_lectures = LectureTmp.objects.filter(open_major=major.major_name).values_list('lecture_code', flat=True).distinct()
            majorlectures_collected = MajorLectureTmp.objects.filter(major_name=major.major_name)
            for ml in majorlectures_collected:
                if ml.lecture_code not in majorlectures_auto_lectures:
                    LectureTmp.objects.create(lecture_code=ml.lecture_code,
                                              lecture_name='',
                                              open_major=ml.major_name,
                                              open_year=ml.start_year,
                                              lecture_type=ml.lecture_type,
                                              is_added=True)
                    cnt_created+=1
        return Response(cnt_created, status=status.HTTP_200_OK)


    # POST /lecture/generate_majorlecture/
    @action(methods=['POST'], detail=False)
    @transaction.atomic
    def generate_majorlecture(self, request):
        created_cnt = 0
        deleted_cnt = 0
        auto_generated_cnt = 0
        # generate majorlecture object from lecturetmp, find start_year, end_year
        majors = Major.objects.all()
        id_cnt = 0
        for major in majors:
            open_department = Department.objects.get(majordepartment__major = major).department_name
            if major.major_name == 'none':
                majorlectures_lecture_codes = LectureTmp.objects.filter(open_major=major.major_name).values_list('lecture_code', flat=True).distinct()
            else:
                majorlectures_lecture_codes = LectureTmp.objects.filter(open_major=major.major_name, open_department=open_department).values_list('lecture_code', flat=True).distinct()
            for lecture_code in majorlectures_lecture_codes:
                if major.major_name == 'none':
                    majorlectures = LectureTmp.objects.filter(open_major=major.major_name,
                                                              lecture_code=lecture_code).order_by('id')
                else:
                    majorlectures = LectureTmp.objects.filter(open_major = major.major_name, open_department=open_department, lecture_code = lecture_code).order_by('id')
                if majorlectures.count() == 0:
                    return Response({"error": "missing"}, status=status.HTTP_400_BAD_REQUEST)
                elif majorlectures.count() == 1:
                    MajorLecture.objects.create(major = major,
                                                lecture = Lecture.objects.get(lecture_code = lecture_code),
                                                start_year = majorlectures.first().open_year,
                                                end_year = 10000,
                                                lecture_type = majorlectures.first().lecture_type)
                    id_cnt += 1;
                else:
                    cnt = 0
                    for majorlecture in majorlectures:
                        MajorLecture.objects.create(major=major,
                                                    lecture=Lecture.objects.get(lecture_code=lecture_code),
                                                    start_year=majorlecture.open_year,
                                                    end_year=10000,
                                                    lecture_type=majorlecture.lecture_type)
                        if cnt != 0:
                            prev_majorlecture = MajorLecture.objects.get(id=id_cnt)
                            if prev_majorlecture.start_year == majorlecture.open_year:
                                prev_majorlecture.end_year = majorlecture.open_year
                            else:
                                prev_majorlecture.end_year = majorlecture.open_year - 1
                            prev_majorlecture.save()
                        cnt += 1
                        id_cnt += 1
        created_cnt = id_cnt

        # generate majorlecture object for major = none, lecture_type = 'major_requirement' or 'major_elective'
        null_majorlectures = MajorLecture.objects.filter(major = Major.objects.get(major_name = 'none'), lecture_type = Lecture.MAJOR_REQUIREMENT)|MajorLecture.objects.filter(major = Major.objects.get(major_name = 'none'), lecture_type = Lecture.MAJOR_ELECTIVE)
        for null_majorlecture in null_majorlectures:
            null_majorlecture_src = LectureTmp.objects.get(open_major = null_majorlecture.major.major_name, lecture_code= null_majorlecture.lecture.lecture_code, open_year = null_majorlecture.start_year, lecture_type = null_majorlecture.lecture_type)
            open_department = Department.objects.get(department_name=null_majorlecture_src.open_department)
            majors = Major.objects.filter(majordepartment__department=open_department)
            for major in majors:
                existing_majorlectures = MajorLecture.objects.filter(major = major, lecture = null_majorlecture.lecture)
                if existing_majorlectures.count() == 0:
                    MajorLecture.objects.create(major=major,
                                                lecture=null_majorlecture.lecture,
                                                start_year=null_majorlecture.start_year,
                                                end_year=null_majorlecture.end_year,
                                                lecture_type=null_majorlecture.lecture_type)
                    auto_generated_cnt += 1
            null_majorlecture.delete()
            deleted_cnt += 1

        data = [created_cnt, deleted_cnt, auto_generated_cnt]
        return Response(data, status=status.HTTP_200_OK)



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

def calculate_by_lecture(user, plan, semesterlectures):
    # order majors(기준: 졸업요구 전공학점 높은 순서)
    majors = Major.objects.filter(planmajor__plan=plan)\
        .annotate(custom_order=Case(When(major_type=Major.SINGLE_MAJOR, then=models.Value(0)),
                                    When(major_type=Major.MAJOR, then=models.Value(1)),
                                    When(major_type=Major.GRADUATE_MAJOR, then=models.Value(2)),
                                    When(major_type=Major.INTERDISCIPLINARY_MAJOR, then=models.Value(3)),
                                    When(major_type=Major.INTERDISCIPLINARY_MAJOR_FOR_TEACHER, then=models.Value(4)),
                                    When(major_type=Major.DOUBLE_MAJOR, then=models.Value(5)),
                                    When(major_type=Major.INTERDISCIPLINARY, then=models.Value(6)),
                                    When(major_type=Major.MINOR, then=models.Value(7)),
                                    When(major_type=Major.INTERDISCIPLINARY_PROGRAM, then=models.Value(8)),
                                    default=models.Value(9),
                                    output_field=models.IntegerField(), ))\
        .order_by('custom_order')

    for semesterlecture in semesterlectures:
        # create variable tmp_majors for use only in loop(1 semesterlecture)
        tmp_majors = majors
        # exclude is_modified = True
        if not semesterlecture.is_modified:
            # subtract credits
            subtract_credits(semesterlecture)

            semester = semesterlecture.semester
            lecture = semesterlecture.lecture

            # calculate lecture_type for each semesterlecture
            # search majorlecture by entrance_year
            if semesterlecture.lecture_type != SemesterLecture.GENERAL:
                major_count = 0
                for major in tmp_majors:
                    if major_count > 1:
                        break

                    candidate_majorlectures = MajorLecture.objects.filter(lecture=lecture, major=major,
                                                                          start_year__lte=user.userprofile.entrance_year,
                                                                          end_year__gte=user.userprofile.entrance_year)\
                        .exclude(lecture_type=MajorLecture.GENERAL).exclude(lecture_type = MajorLecture.GENERAL_ELECTIVE)\
                        .order_by('-lecture_type')

                    if candidate_majorlectures.count() !=0:
                        if major_count == 0:
                            semesterlecture.lecture_type = candidate_majorlectures.first().lecture_type
                            semesterlecture.lecture_type1 = candidate_majorlectures.first().lecture_type
                            semesterlecture.recognized_major1 = major
                            semesterlecture.save()
                        elif major_count == 1:
                            semesterlecture.lecture_type2 = candidate_majorlectures.first().lecture_type
                            semesterlecture.recognized_major2 = major
                            semesterlecture.save()
                        major_count += 1

                if major_count != 2:
                    if major_count == 1:
                        tmp_majors = tmp_majors.exclude(id=semesterlecture.recognized_major1.id)
                    # search majorlecture by semester.year
                    for major in tmp_majors:
                        if major_count > 1:
                            break

                        candidate_majorlectures = MajorLecture.objects.filter(lecture=lecture, major=major,
                                                                              start_year__lte=semester.year,
                                                                              end_year__gte=semester.year)\
                            .exclude(lecture_type=MajorLecture.GENERAL).exclude(lecture_type = MajorLecture.GENERAL_ELECTIVE)\
                            .order_by('-lecture_type')
                        if candidate_majorlectures.count() != 0:
                            if major_count == 0:
                                semesterlecture.lecture_type = candidate_majorlectures.first().lecture_type
                                semesterlecture.lecture_type1 = candidate_majorlectures.first().lecture_type
                                semesterlecture.recognized_major1 = major
                                semesterlecture.save()
                            elif major_count == 1:
                                semesterlecture.lecture_type2 = candidate_majorlectures.first().lecture_type
                                semesterlecture.recognized_major2 = major
                                semesterlecture.save()
                            major_count += 1

                if major_count == 1:
                    semesterlecture.lecture_type2 = SemesterLecture.NONE
                    semesterlecture.recognized_major2 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                    semesterlecture.save()
                elif major_count == 0:
                    semesterlecture.lecture_type = SemesterLecture.GENERAL_ELECTIVE
                    semesterlecture.lecture_type1 = SemesterLecture.GENERAL_ELECTIVE
                    semesterlecture.recognized_major1 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                    semesterlecture.lecture_type2 = SemesterLecture.NONE
                    semesterlecture.recognized_major2 = Major.objects.get(id=SemesterLecture.DEFAULT_MAJOR_ID)
                    semesterlecture.save()

            # calculate credit for each semesterlecture

            # lecturecredits = LectureCredit.objects.filter(lecture=lecture,
            #                                               start_year__lte=user.userprofile.entrance_year,
            #                                               end_year__gte=user.userprofile.entrance_year)
            # if lecturecredits.count() == 0:
            #     lecturecredits = LectureCredit.objects.filter(lecture=lecture,
            #                                                   start_year__lte=semester.year,
            #                                                   end_year__gte=semester.year)
            lecturecredits = LectureCredit.objects.filter(lecture=lecture,
                                                          start_year__lte=semester.year,
                                                          end_year__gte=semester.year)

            if lecturecredits.count() > 0:
                semesterlecture.credit = lecturecredits.first().credit
                semesterlecture.save()

             # add credits
            add_credits(semesterlecture)


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

