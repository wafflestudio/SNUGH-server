from django.db.models import Case, When, Q
from django.db import transaction
from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from lecture.models import * 
from lecture.serializers import *
from user.models import *
from requirement.models import *
from django.core.paginator import Paginator
from django.db.models.functions import Length
from django.db.models import F, Prefetch
from snugh.permissions import IsOwnerOrCreateReadOnly
from snugh.exceptions import DuplicationError, NotOwner
from lecture.utils import add_credits, subtract_credits, add_semester_credits, sub_semester_credits
from lecture.const import *
from lecture.utils import update_lecture_info


class PlanViewSet(viewsets.GenericViewSet, generics.RetrieveUpdateDestroyAPIView):
    """
    Generic ViewSet of Plan Object
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer 
    permission_classes = [IsOwnerOrCreateReadOnly]

    # POST /plan
    @transaction.atomic
    def create(self, request):
        """Create new plan"""
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        planmajor = PlanMajorCreateSerializer(data={'plan':plan.id}, context={'request':request})
        planmajor.is_valid(raise_exception=True)
        planmajor.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /plan/:planId
    @transaction.atomic
    def update(self, request, pk=None):
        """Update user's plan"""
        return super().update(request, pk)
    
    # DEL /plan/:planId
    def destroy(self, request, pk=None):
        """Delete user's plan"""
        return super().destroy(request, pk)

    # GET /plan/:planId
    def retrieve(self, request, pk=None):
        """Retrieve user's plan"""
        return super().retrieve(request, pk)

    # GET /plan
    def list(self, request):
        """Get user's plans list"""
        user = request.user
        plans = user.plan.all()
        return Response(self.get_serializer(plans, many=True).data, status=status.HTTP_200_OK)

    # 강의구분 자동계산
    # PUT /plan/:planId/calculate
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def calculate(self, request, pk=None):
        """Calculate credits"""

        plan = update_lecture_info(request.user, pk)
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /plan/:planId/major
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def major(self, request, pk=None):
        """Update plan's majors"""

        plan = self.get_object()
        # overwrite planmajors, planrequirements
        plan.planmajor.all().delete()
        plan.planrequirement.all().delete()
        planmajor = PlanMajorCreateSerializer(data={'plan':plan.id}, context={'request':request})
        planmajor.is_valid(raise_exception=True)
        planmajor.save()
        self.calculate(request, pk=pk)
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /plan/:planId/copy
    @action(detail=True, methods=['POST'])
    @transaction.atomic
    def copy(self, request, pk=None):
        """Copy existing plan"""
        try:
            plan = Plan.objects.prefetch_related(
                'user', 
                'planmajor', 
                'planrequirement', 
                'semester',
                'planmajor__major',
                'planrequirement__requirement',
                'semester__semesterlecture',
                'semester__semesterlecture__lecture',
                'semester__semesterlecture__recognized_major1',
                'semester__semesterlecture__recognized_major2'
                ).get(id=pk)
            user = plan.user
        except Plan.DoesNotExist:
            raise NotFound()
        if request.user != plan.user:
            raise NotOwner()
        new_plan = Plan.objects.create(user=user, plan_name=f"{plan.plan_name} (복사본)")

        planmajors = plan.planmajor.all()
        new_planmajors = []
        for planmajor in planmajors:
            new_planmajors.append(PlanMajor(plan=new_plan, major=planmajor.major))
        PlanMajor.objects.bulk_create(new_planmajors)

        planrequirements = plan.planrequirement.all()
        new_planrequirements = []
        for planrequirement in planrequirements:
            new_planrequirements.append(PlanRequirement(plan=new_plan, requirement=planrequirement.requirement, required_credit=planrequirement.required_credit))
        PlanRequirement.objects.bulk_create(new_planrequirements)

        semesters = plan.semester.all()
        for semester in semesters:
            new_semester = Semester.objects.create(plan=new_plan,
                                                   year=semester.year,
                                                   semester_type=semester.semester_type,
                                                   major_requirement_credit=semester.major_requirement_credit,
                                                   major_elective_credit=semester.major_elective_credit,
                                                   general_credit=semester.general_credit,
                                                   general_elective_credit=semester.general_elective_credit)

            semesterlectures = semester.semesterlecture.all()
            new_semesterlectures = []
            for semesterlecture in semesterlectures:
                new_semesterlectures.append(SemesterLecture(semester=new_semester,
                                               lecture=semesterlecture.lecture,
                                               lecture_type=semesterlecture.lecture_type,
                                               recognized_major1=semesterlecture.recognized_major1,
                                               lecture_type1=semesterlecture.lecture_type1,
                                               recognized_major2=semesterlecture.recognized_major2,
                                               lecture_type2=semesterlecture.lecture_type2,
                                               credit=semesterlecture.credit,
                                               recent_sequence=semesterlecture.recent_sequence,
                                               is_modified=semesterlecture.is_modified))
            SemesterLecture.objects.bulk_create(new_semesterlectures)
        serializer = self.get_serializer(new_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SemesterViewSet(viewsets.GenericViewSet, generics.RetrieveDestroyAPIView):
    """
    Generic ViewSet of Semester Object
    """
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    permission_classes = [IsOwnerOrCreateReadOnly]

    # POST /semester
    @transaction.atomic
    def create(self, request):
        """Create new semester"""
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        plan = Plan.objects.get(id=data['plan'])
        if plan.user != request.user:
            raise NotOwner()
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /semester/:semesterId
    @transaction.atomic
    def update(self, request, pk=None):
        """Update semester"""
        data = request.data
        semester = self.get_object()
        year = data.get('year')
        semester_type = data.get('semester_type')
        if not (year or semester_type):
            raise FieldError("body is empty")
        serializer = self.get_serializer(semester, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semester, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # DEL /semester/:semesterId
    def destroy(self, request, pk=None):
        """Destroy semester"""
        return super().destroy(request, pk)
    
    # GET /semester/:semesterId
    def retrieve(self, request, pk=None):
        """Retrieve semester"""
        return super().retrieve(request, pk)

class LectureViewSet(viewsets.GenericViewSet):
    queryset = SemesterLecture.objects.all()
    serializer_class = SemesterLectureSerializer
    #permission_classes = [IsOwnerOrCreateReadOnly]

    # POST /lecture
    @transaction.atomic
    def create(self, request):
        """Create semester lecture"""
        semester_id = request.data.get('semester_id')
        lecture_id_list = request.data.get('lecture_id')
        try:
            semester = Semester.objects.select_related('plan').prefetch_related('semesterlecture').get(id=semester_id)
        except Semester.DoesNotExist:
            raise NotFound('semester does not exist')
        plan = semester.plan
        lecture_id_list = list(set(map(lambda x: int(x), lecture_id_list)))
        if set(lecture_id_list) & set(plan.semester.values_list('semesterlecture__lecture', flat=True)):
            raise DuplicationError('some lecture already exists in plan.')

        lecture_in_semester = semester.semesterlecture.all()
        n_lectures = lecture_in_semester.count()

        default_major = Major.objects.get(id=DEFAULT_MAJOR_ID)
        semesterlectures=[]
        for i, lecture_id in enumerate(lecture_id_list):
            try :
                lecture = Lecture.objects.get(id=lecture_id)
            except Lecture.DoesNotExist:
                raise NotFound('lecture does not exist')
            lecture_type = lecture.lecture_type
            recognized_major = default_major
            
            sl = SemesterLecture.objects.create(
                semester=semester,
                lecture=lecture,
                lecture_type=lecture_type,
                recognized_major1=recognized_major,
                lecture_type1=lecture_type,
                credit=lecture.credit,
                recent_sequence=n_lectures+i)
            semesterlectures.append(sl)       
            semester = add_semester_credits(sl, semester)

        update_lecture_info(request.user, plan.id, semesterlectures, semester)
        data = SemesterSerializer(semester).data
        return Response(data, status=status.HTTP_201_CREATED)
    
    # PUT /lecture/:semesterlectureId/position
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def position(self, request, pk=None):
        """Position semester lecture"""
        #TODO: API 문서 수정 -> lecture_id가 아닌 semesterlecture_id로 / request 형식 변경 
        target_lecture = SemesterLecture.objects.select_related('semester').get(pk=pk)
        semester_to = request.data.get('semester_to', None)
        semester_from = target_lecture.semester
        position = request.data.get('position', 0)
        if not semester_to:
            raise FieldError("'semester_to' field missing")
        position_prev = target_lecture.recent_sequence
        semester_from_lectures = semester_from.semesterlecture.filter(recent_sequence__gt=position_prev).order_by('recent_sequence')
        try:
            semester_to = Semester.objects.prefetch_related(
                Prefetch(
                    'semesterlecture', 
                    queryset=SemesterLecture.objects.filter(recent_sequence__gte=position).order_by('recent_sequence'), 
                    to_attr='semester_to_lectures')).get(id=semester_to)
        except Semester.DoesNotExist:
            raise NotFound('semester does not exist')
        semester_to_lectures = semester_to.semester_to_lectures

        if not (0<=position<=len(semester_to_lectures)):
            raise FieldError("position out of range")
        semester_from = sub_semester_credits(target_lecture, semester_from)
        target_lecture.semester = semester_to
        target_lecture.recent_sequence = position
        semester_to = add_semester_credits(target_lecture, semester_to)
        Semester.objects.bulk_update(
            [semester_from, semester_to], 
            fields=[
                'major_requirement_credit', 
                'major_elective_credit', 
                'general_credit', 
                'general_elective_credit'])
        sl_list = []
        for sl in semester_from_lectures:
            sl.recent_sequence-=1
            sl_list.append(sl)
        for sl in semester_to_lectures:
            sl.recent_sequence+=1
            sl_list.append(sl)
        semesterlectures = sl_list + [target_lecture]
        SemesterLecture.objects.bulk_update(semesterlectures, fields=['recent_sequence', 'semester'])
        
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
        updated_semester = subtract_credits(semesterlecture)
        updated_semester.save()

        semesterlecture.credit = credit
        semesterlecture.is_modified = True
        semesterlecture.save()

        updated_semester = add_credits(semesterlecture)
        updated_semester.save()

        data = SemesterLectureSerializer(semesterlecture).data
        return Response(data, status=status.HTTP_200_OK)


    # PUT /lecture/:semesterLectureId/recognized_major
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def recognized_major(self, request, pk=None):
        semesterlecture = self.get_object()
        lecture_type = request.data.get('lecture_type', None)
        user = request.user

        updated_semester = subtract_credits(semesterlecture)
        updated_semester.save()

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

            updated_semester = add_credits(semesterlecture)
            updated_semester.save()

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

            updated_semester = add_credits(semesterlecture)
            updated_semester.save()

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

            updated_semester = add_credits(semesterlecture)
            updated_semester.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"error": "wrong lecture_type"}, status=status.HTTP_400_BAD_REQUEST)

    # DEL /lecture/:semlectureId
    @transaction.atomic
    def destroy(self, request, pk=None):
        """Destroy semester lecture"""
        semesterlecture = SemesterLecture.objects.select_related('semester').get(pk=pk)
        semester = sub_semester_credits(semesterlecture, semesterlecture.semester)
        semester.save()
        semesterlecture.delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 

    # GET /lecture/?search_type=(string)&search_keyword=(string)&major=(string)&credit=(string)
    # TODO: n-gram 서치 고도화
    def list(self, request):
        
        page = request.GET.get('page', '1')
        search_type = request.query_params.get("search_type")
        search_year = request.query_params.get("search_year")
        search_keyword = request.query_params.get("search_keyword")
        plan_id = request.query_params.get("plan_id")
        if not (search_type and search_year and plan_id):
            raise FieldError('query parameter missing [search_type, search_year, plan_id]')
        try:
            existing_lectures = list(Plan.objects.get(id=plan_id).semester.values_list('semesterlecture__lecture', flat=True))
        except Plan.DoesNotExist:
            raise NotFound()
        search_year = int(search_year)
        # Case 1: major requirement or major elective
        if search_type in [MAJOR_REQUIREMENT, MAJOR_ELECTIVE]:
            major_name = request.query_params.get("major_name")
            if major_name:
                year_standard = search_year if search_year < UPDATED_YEAR else UPDATED_YEAR-2
                depeqv_name = DepartmentEquivalent.objects.filter(major_name=major_name).values_list('department_name', flat=True)
                majoreqv_names = MajorEquivalent.objects.filter(major_name=major_name).values_list('equivalent_major_name', flat=True)
                major_names = [major_name] + list(majoreqv_names)
                lectures = Lecture.objects.filter(
                    (Q(open_major__in=major_names) | Q(open_department__in=depeqv_name)), 
                    lecture_type=search_type, recent_open_year__gte=year_standard)\
                    .exclude(id__in=existing_lectures).order_by('lecture_name', 'recent_open_year')
            else: 
                raise FieldError('query parameter missing [major_name]')

        # Case 2: keyword
        else:
            if search_keyword:
                year_standard = search_year if search_year < UPDATED_YEAR else UPDATED_YEAR-2
                lectures = Lecture.objects.search(search_keyword)\
                    .filter(recent_open_year__gte = year_standard)\
                    .exclude(id__in=existing_lectures)\
                    .annotate(
                        first_letter=Case(
                            When(lecture_name__startswith=search_keyword[0], 
                                then=models.Value(0)),
                            default=models.Value(1),
                            output_field=models.IntegerField(),),
                        icontains_priority=Case(
                            When(lecture_name__icontains=search_keyword, 
                                then=models.Value(0)),
                            default=models.Value(1),
                            output_field=models.IntegerField(),),
                        priority = F('first_letter')+F('icontains_priority'),
                        match_rate=Length('lecture_name'))\
                    .order_by('priority', 'match_rate', 'recent_open_year', 'lecture_name')
            else:
                return Response([], status=status.HTTP_200_OK)
        
        lectures = Paginator(lectures, 20).get_page(page)
        serializer = LectureSerializer(lectures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
                id_cnt+=1
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

