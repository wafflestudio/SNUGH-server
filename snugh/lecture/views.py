from django.db.models import Case, When, Q, Value, IntegerField, F, Prefetch
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
from snugh.permissions import IsOwnerOrCreateReadOnly
from snugh.exceptions import DuplicationError, NotOwner
from lecture.utils import *
from lecture.const import *


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
                ).get(pk=pk)
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
    """
    Generic ViewSet of SemesterLecture Object
    """
    queryset = SemesterLecture.objects.all()
    serializer_class = SemesterLectureSerializer
    permission_classes = [IsOwnerOrCreateReadOnly]

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
            raise FieldError("Field missing [semester_to]")
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
        """Change semester lecture credit"""
        credit = request.data.get('credit', 0)
        if not 0<credit<5 :
            raise FieldError("Invalid field [credit]")
        try:
            semesterlecture = SemesterLecture.objects.select_related(
                'semester',
                'recognized_major1',
                'recognized_major2',
                'lecture'
            ).get(pk=pk)
        except SemesterLecture.DoesNotExist:
            raise NotFound("semesterlecture does not exist")

        semester = semesterlecture.semester
        if credit == semesterlecture.credit:
            return Response(SemesterLectureSerializer(semesterlecture).data, status=status.HTTP_200_OK)

        credit_history_generator(request.user, semesterlecture, credit)
        semester = sub_semester_credits(semesterlecture, semester)
        semesterlecture.credit = credit
        semesterlecture.is_modified = True
        semesterlecture.save()
        semester = add_semester_credits(semesterlecture, semester)
        semester.save()

        data = SemesterLectureSerializer(semesterlecture).data
        return Response(data, status=status.HTTP_200_OK)

    # PUT /lecture/:semesterLectureId/recognized_major
    @action(methods=['PUT'], detail=True)
    @transaction.atomic
    def recognized_major(self, request, pk=None):
        """Change semester lecture major, major_type, lecture_type"""
        semesterlecture = SemesterLecture.objects.select_related(
            'semester', 
            'lecture',
            'recognized_major1',
            'recognized_major2').get(pk=pk)
        lecture_type = request.data.get('lecture_type', None)
        user = request.user
        semester = semesterlecture.semester
        semester = sub_semester_credits(semesterlecture, semester)

        if lecture_type in [GENERAL, GENERAL_ELECTIVE]:
            lecturetype_history_generator(user, semesterlecture, lecture_type)
            data = {
                "lecture_type": lecture_type,
                "recognized_major1": DEFAULT_MAJOR_ID,
                "recognized_major2": DEFAULT_MAJOR_ID,
                "lecture_type1": lecture_type,
                "lecture_type2": NONE,
                "is_modified": True
            }

        elif lecture_type in [MAJOR_ELECTIVE, MAJOR_REQUIREMENT]:
            try:
                recognized_major1 = Major.objects.get(
                    major_name=request.data.get('recognized_major_name1'),
                    major_type=request.data.get('recognized_major_type1'))
                recognized_major2 = Major.objects.get(
                    major_name=request.data.get('recognized_major_name2', DEFAULT_MAJOR_NAME),
                    major_type=request.data.get('recognized_major_type2', DEFAULT_MAJOR_TYPE))
            except Major.DoesNotExist:
                raise NotFound()
            lecture_type1 = request.data.get('lecture_type1', NONE) 
            lecture_type2 = request.data.get('lecture_type2', NONE)
            lecturetype_history_generator(
                user, 
                semesterlecture, 
                lecture_type, 
                [recognized_major1, recognized_major2],
                [lecture_type1, lecture_type2])
            data = {
                "lecture_type": lecture_type, 
                "recognized_major1": recognized_major1.id,
                "recognized_major2": recognized_major2.id,
                "lecture_type1": lecture_type1, 
                "lecture_type2": lecture_type2,
                "is_modified": True
            }

        else:
            raise FieldError("Invalid field [lecture_type]")

        serializer = self.get_serializer(semesterlecture, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(semesterlecture, serializer.validated_data)

        semester = add_semester_credits(semesterlecture, semester)
        semester.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

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
                                then=Value(0)),
                            default=Value(1),
                            output_field=IntegerField(),),
                        icontains_priority=Case(
                            When(lecture_name__icontains=search_keyword, 
                                then=Value(0)),
                            default=Value(1),
                            output_field=IntegerField(),),
                        priority = F('first_letter')+F('icontains_priority'),
                        match_rate=Length('lecture_name'))\
                    .order_by('priority', 'match_rate', 'recent_open_year', 'lecture_name')
            else:
                return Response([], status=status.HTTP_200_OK)
        
        lectures = Paginator(lectures, 20).get_page(page)
        serializer = LectureSerializer(lectures, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
