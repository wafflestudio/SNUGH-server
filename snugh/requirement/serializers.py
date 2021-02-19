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
        data = []

        earned_credit = 0
        for e in PlanRequirement.objects.filter(plan_id=plan.id):
            earned_credit += e.earned_credit

        required_credit = 0
        for e in Requirement.objects.all():
            required_credit += e.required_credit

        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return ProgressDetailSerializer(data).data

    def get_major_requirement(self, plan):
        data = []

        required_credit = None
        earned_credit = None
        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return ProgressDetailSerializer(data).data

    def get_major_elective(self, plan):
        data = []

        required_credit = None
        earned_credit = None
        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return ProgressDetailSerializer(data).data

    def get_general(self, plan):
        data = []

        required_credit = None
        earned_credit = None
        progress = earned_credit / required_credit

        data['required_credit'] = required_credit
        data['earned_credit'] = earned_credit
        data['progress'] = progress
        return ProgressDetailSerializer(data).data


class ProgressDetailSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'required_credit',
            'earned_credit',
            'progress'
        )
