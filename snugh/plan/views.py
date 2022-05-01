
from django.db import transaction
from rest_framework import status, viewsets, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from snugh.permissions import IsOwnerOrCreateReadOnly
from snugh.exceptions import NotOwner, NotFound
from lecture.utils import update_lecture_info
from plan.serializers import PlanSerializer, PlanMajorCreateSerializer
from plan.models import Plan, PlanMajor
from semester.models import Semester
from requirement.models import PlanRequirement
from lecture.models import SemesterLecture

class PlanViewSet(viewsets.GenericViewSet, generics.RetrieveUpdateDestroyAPIView):
    """
    Generic ViewSet of Plan Object.
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer 
    permission_classes = [IsOwnerOrCreateReadOnly]

    # POST /plan
    @transaction.atomic
    def create(self, request):
        """Create new plan."""
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
        """Update user's plan."""
        return super().update(request, pk)
    
    # DEL /plan/:planId
    def destroy(self, request, pk=None):
        """Delete user's plan."""
        return super().destroy(request, pk)

    # GET /plan/:planId
    def retrieve(self, request, pk=None):
        """Retrieve user's plan."""
        return super().retrieve(request, pk)

    # GET /plan
    def list(self, request):
        """Get user's plans list."""
        user = request.user
        plans = user.plan.all()
        return Response(self.get_serializer(plans, many=True).data, status=status.HTTP_200_OK)

    # 강의구분 자동계산
    # PUT /plan/:planId/calculate
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def calculate(self, request, pk=None):
        """Calculate credits."""
        plan = update_lecture_info(request.user, pk)
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /plan/:planId/major
    @action(detail=True, methods=['PUT'])
    @transaction.atomic
    def major(self, request, pk=None):
        """Update plan's majors."""
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
        """Copy existing plan."""
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
