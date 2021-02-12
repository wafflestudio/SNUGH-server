from rest_framework import serializers
from requirement.models import Requirement, PlanRequirement

class RequirementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Requirement
        fields = (
            'id',
            'description',
            'is_fulfilled',
            'is_credit_requirement',
            'requirement_type',
            'requirement_type_detail',
            'requirement_type_detail_detail',
            'required_credit',
            'earned_credit'
        )

class ProgressSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanRequirement
        fields = (
            'required_credit',
            'earned_credit',
            'progress'
        )