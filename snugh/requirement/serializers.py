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


class ProgressSerializer(serializers.ModelSerializer):
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
        data = {}

        planrequirement = PlanRequirement.objects.filter(plan_id=plan.id)
        earned_credit = 0
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        requirement = Requirement.objects.filter(planrequirement__plan_id=plan.id)
        required_credit = 0
        for r in requirement:
            required_credit += r.required_credit

        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return data

    def get_major_requirement(self, plan):
        data = {}

        planrequirement = PlanRequirement.objects.filter(plan_id=plan.id, requirement__requirement_type="major_requirement")
        earned_credit = 0
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        requirement = Requirement.objects.filter(planrequirement__plan_id=plan.id, requirement_type="major_requirement")
        required_credit = 0
        for r in requirement:
            required_credit += r.required_credit

        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return data

    def get_major_elective(self, plan):
        data = {}

        planrequirement = PlanRequirement.objects.filter(plan_id=plan.id, requirement__requirement_type="major_elective")
        earned_credit = 0
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        requirement = Requirement.objects.filter(planrequirement__plan_id=plan.id, requirement_type="major_elective")
        required_credit = 0
        for r in requirement:
            required_credit += r.required_credit

        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return data

    def get_general(self, plan):
        data = {}

        planrequirement = PlanRequirement.objects.filter(plan_id=plan.id, requirement__requirement_type="general")
        earned_credit = 0
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        requirement = Requirement.objects.filter(planrequirement__plan_id=plan.id, requirement_type="general")
        required_credit = 0
        for r in requirement:
            required_credit += r.required_credit

        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return data