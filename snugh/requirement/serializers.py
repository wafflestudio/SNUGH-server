from rest_framework import serializers
from requirement.models import Requirement, PlanRequirement
from lecture.models import PlanMajor


class RequirementSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    is_credit_requirement = serializers.SerializerMethodField()
    requirement_type = serializers.SerializerMethodField()
    requirement_type_detail = serializers.SerializerMethodField()
    requirement_type_detail_detail = serializers.SerializerMethodField()
    required_credit = serializers.SerializerMethodField()

    class Meta:
        model = PlanRequirement
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
        requirement = plan_requirement.requirement
        return requirement.id

    def get_description(self, plan_requirement):
        requirement = plan_requirement.requirement
        return requirement.description

    def get_is_credit_requirement(self, plan_requirement):
        requirement = plan_requirement.requirement
        return requirement.is_credit_requirement

    def get_requirement_type(self, plan_requirement):
        requirement = plan_requirement.requirement
        return requirement.requirement_type

    def get_requirement_type_detail(self, plan_requirement):
        requirement = plan_requirement.requirement
        return requirement.requirement_type_detail

    def get_requirement_type_detail_detail(self, plan_requirement):
        requirement = plan_requirement.requirement
        return requirement.requirement_type_detail_detail

    def get_required_credit(self, plan_requirement):
        requirement = plan_requirement.requirement
        return requirement.required_credit


class ProgressSerializer(serializers.ModelSerializer):
    major_name = serializers.SerializerMethodField()
    major_type = serializers.SerializerMethodField()
    all = serializers.SerializerMethodField()
    major_requirement = serializers.SerializerMethodField()
    major_elective = serializers.SerializerMethodField()
    general = serializers.SerializerMethodField()

    class Meta:
        model = PlanMajor
        fields = (
            'major_name',
            'major_type',
            'all',
            'major_requirement',
            'major_elective',
            'general',
        )

    def get_major_name(self, planmajor):
        return planmajor.major.major_name

    def get_major_type(self, planmajor):
        return planmajor.major.major_type

    def get_all(self, planmajor):
        plan = planmajor.plan
        major = planmajor.major

        # 이수 학점 계산하기
        earned_credit = 0
        planrequirement = PlanRequirement.objects.filter(plan=plan,
                                                         requirement__major=major)
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        # 기준 학점 계산하기
        required_credit = 0
        requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                 major=major)
        for r in requirement:
            required_credit += r.required_credit

        # 이수 비율 계산하기
        if required_credit:
            progress = round(earned_credit / required_credit, 2)
        else:
            progress = 0.0

        data = {'required_credit': required_credit, 'earned_credit': earned_credit, 'progress': progress}
        return data

    def get_major_requirement(self, planmajor):
        plan = planmajor.plan
        major = planmajor.major

        # 이수 학점 계산하기
        earned_credit = 0
        planrequirement = PlanRequirement.objects.filter(plan=plan,
                                                         requirement__major=major,
                                                         requirement__requirement_type=Requirement.MAJOR_REQUIREMENT)
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        # 기준 학점 계산하기
        required_credit = 0
        requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                 major=major,
                                                 requirement_type=Requirement.MAJOR_REQUIREMENT)
        for r in requirement:
            required_credit += r.required_credit

        # 이수 비율 계산하기
        if required_credit:
            progress = round(earned_credit / required_credit, 2)
        else:
            progress = 0.0

        data = {'required_credit': required_credit, 'earned_credit': earned_credit, 'progress': progress}
        return data

    def get_major_elective(self, planmajor):
        plan = planmajor.plan
        major = planmajor.major

        # 이수 학점 계산하기
        earned_credit = 0
        planrequirement = PlanRequirement.objects.filter(plan=plan,
                                                         requirement__major=major,
                                                         requirement__requirement_type=Requirement.MAJOR_ELECTIVE)
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        # 기준 학점 계산하기
        required_credit = 0
        requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                 major=major,
                                                 requirement_type=Requirement.MAJOR_ELECTIVE)
        for r in requirement:
            required_credit += r.required_credit

        # (교직을 전선에 포함) 이수 학점 계산하기
        planrequirement = PlanRequirement.objects.filter(plan=plan,
                                                         requirement__major=major,
                                                         requirement__requirement_type=Requirement.TEACHING)
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        # (교직을 전선에 포함) 기준 학점 계산하기
        requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                 major=major,
                                                 requirement_type=Requirement.TEACHING)
        for r in requirement:
            required_credit += r.required_credit

        # 이수 비율 계산하기
        if required_credit:
            progress = round(earned_credit / required_credit, 2)
        else:
            progress = 0.0

        data = {'required_credit': required_credit, 'earned_credit': earned_credit, 'progress': progress}
        return data

    def get_general(self, planmajor):
        plan = planmajor.plan
        major = planmajor.major

        # 이수 학점 계산하기
        earned_credit = 0
        planrequirement = PlanRequirement.objects.filter(plan=plan,
                                                         requirement__major=major,
                                                         requirement__requirement_type=Requirement.GENERAL)
        for pr in planrequirement:
            earned_credit += pr.earned_credit

        # 기준 학점 계산하기
        required_credit = 0
        requirement = Requirement.objects.filter(planrequirement__plan=plan,
                                                 major=major,
                                                 requirement_type=Requirement.GENERAL)
        for r in requirement:
            required_credit += r.required_credit

        # 이수 비율 계산하기
        if required_credit:
            progress = round(earned_credit / required_credit, 2)
        else:
            progress = 0.0

        data = {'required_credit': required_credit, 'earned_credit': earned_credit, 'progress': progress}
        return data
