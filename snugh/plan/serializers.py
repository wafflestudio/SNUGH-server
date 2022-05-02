from rest_framework import serializers
from django.db.models import Case, When, IntegerField, Value
from plan.models import Plan
from user.serializers import MajorSerializer
from semester.serializers import SemesterSerializer
from semester.const import *


class PlanRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for certain plan's details."""
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
        

class PlanSerializer(serializers.ModelSerializer):
    """Serializer for plans' overviews."""
    majors = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            'id',
            'plan_name',
            'majors',
        )
    
    def create(self, validated_data):
        user = self.context['request'].user
        plan_name = validated_data.get('plan_name')
        return Plan.objects.create(user=user, plan_name=plan_name)

    def get_majors(self, plan):
        planmajors = plan.planmajor.select_related('major').all()
        majors = [planmajor.major for planmajor in planmajors]
        return MajorSerializer(majors, many=True).data
