from rest_framework import serializers
from django.db.models import Case, When, IntegerField, Value
from plan.models import Plan, PlanMajor
from requirement.models import PlanRequirement
from user.serializers import MajorSerializer
from semester.serializers import SemesterSerializer
from snugh.exceptions import FieldError, NotFound
from user.models import Major
from semester.const import *


class PlanSerializer(serializers.ModelSerializer):
    majors = serializers.SerializerMethodField()
    semesters = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            'id',
            'user',
            'plan_name',
            'majors',
            'semesters',
        )
    
    def get_majors(self, plan):
        planmajors = plan.planmajor.select_related('major').all()
        majors = [planmajor.major for planmajor in planmajors]
        return MajorSerializer(majors, many=True).data

    def get_semesters(self, plan):
        semesters = plan.semester.annotate(semester_value=Case(
            When(semester_type=FIRST, then=Value(0)),
            When(semester_type=SUMMER, then=Value(1)),
            When(semester_type=SECOND, then=Value(2)),
            When(semester_type=WINTER, then=Value(3)),
            output_field=IntegerField()
        )).order_by('year', 'semester_value')
        return SemesterSerializer(semesters, many=True).data

    def create(self, validated_data):
        user = self.context['request'].user
        plan_name = validated_data.get('plan_name', '새로운 계획')
        return Plan.objects.create(user=user, plan_name=plan_name)


class PlanMajorCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanMajor 
        fields = ('plan',)

    def create(self, validated_data):
        majors = validated_data['majors']
        plan = validated_data['plan']
        user = self.context['request'].user
        std = user.userprofile.entrance_year
        planmajors = []
        planrequirements = []
        for major in majors:
            planmajors.append(PlanMajor(plan=plan, major=major))
            requirements = major.requirement.filter(start_year__lte=std, end_year__gte=std)
            for requirement in requirements:
                planrequirements.append(PlanRequirement(plan=plan, 
                                                        requirement=requirement, 
                                                        required_credit=requirement.required_credit))
        PlanRequirement.objects.bulk_create(planrequirements)
        return PlanMajor.objects.bulk_create(planmajors)

    def validate(self, data):
        majors = self.context['request'].data.get('majors')
        if not majors:
            raise FieldError("Field missing [majors]")
        major_instances = []
        for major in majors:
            major_name = major.get('major_name')
            major_type = major.get('major_type')
            if not (major_name and major_type):
                raise FieldError("Field missing [major_name, major_type]")
            try:
                major_instances.append(Major.objects.get(major_name=major_name, major_type=major_type))
            except Major.DoesNotExist:
                raise NotFound("Does not exist [Major]")
        data['majors'] = major_instances
        return data