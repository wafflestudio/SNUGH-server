from rest_framework import serializers
from core.requirement.models import PlanRequirement

# TODO: Comments about serializers.

class RequirementSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_credit_requirement = serializers.SerializerMethodField()
    requirement_type = serializers.SerializerMethodField()
    required_credit = serializers.SerializerMethodField()

    class Meta:
        model = PlanRequirement
        fields = (
            'id',
            'description',
            'is_credit_requirement',
            'requirement_type',
            'required_credit',
            'earned_credit'
        )

    def get_id(self, plan_requirement):
        return plan_requirement.requirement.id

    def get_description(self, plan_requirement):
        return plan_requirement.requirement.description

    def get_is_credit_requirement(self, plan_requirement):
        return plan_requirement.requirement.is_credit_requirement

    def get_requirement_type(self, plan_requirement):
        return plan_requirement.requirement.requirement_type

    def get_required_credit(self, plan_requirement): 
        return plan_requirement.requirement.required_credit
