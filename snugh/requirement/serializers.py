from rest_framework import serializers
from requirement.models import Requirement, PlanRequirement
from lecture.models import Plan

class RequirementSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_credit_requirement = serializers.SerializerMethodField()
    requirement_type = serializers.SerializerMethodField()
    requirement_type_detail = serializers.SerializerMethodField()
    requirement_type_detail_detail = serializers.SerializerMethodField()
    required_credit = serializers.SerializerMethodField()

    class Meta:
        Model = PlanRequirement
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

    def get_id(self, plan_requirement):
        return plan_requirement.plan_id

    def get_description(self, plan_requirement):
        requirement = Requirement.objects.get(pk=plan_requirement.plan_id)
        return requirement.description

    def get_is_credit_requirement(self, plan_requirement):
        requirement = Requirement.objects.get(pk=plan_requirement.plan_id)
        return requirement.is_credit_requirement

    def get_requirement_type(self, plan_requirement):
        requirement = Requirement.objects.get(pk=plan_requirement.plan_id)
        return requirement.requirement_type

    def get_requirement_type_detail(self, plan_requirement):
        requirement = Requirement.objects.get(pk=plan_requirement.plan_id)
        return requirement.requirement_type_detail

    def get_requirement_type_detail_detail(self, plan_requirement):
        requirement = Requirement.objects.get(pk=plan_requirement.plan_id)
        return requirement.requirement_type_detail_detail

    def get_required_credit(self, plan_requirement):
        requirement = Requirement.objects.get(pk=plan_requirement.plan_id)
        return requirement.required_credit

class ProgressSerializer(serializers.ModelSerializer): # 미완성
    all = serializers.SerializerMethodField()
    major_requirement = serializers.SerializerMethodField()
    major_elective = serializers.SerializerMethodField()
    general = serializers.SerializerMethodField()

    class Meta:
        Model = Plan
        fields = (
            'all',
            'major_requirement',
            'major_elective',
            'general'
        )

    def get_all(self, plan):
        return None

    def get_major_requirement(self, plan):
        return None

    def get_major_elective(self, plan):
        return None

    def get_general(self, plan):
        return None

class ProgressDetailSerializer(serializers.ModelSerializer): # 미완성
    required_credit = serializers.SerializerMethodField()
    earned_credit = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'required_credit',
            'earned_credit',
            'progress'
        )
