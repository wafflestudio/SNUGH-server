from django.db import models
from user.models import Major
from lecture.models import Plan


class Requirement(models.Model):
    # 구분 없음
    NONE = 'none'  

    # Requirement Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ALL = 'major_all'  # 전공 전체
    GENERAL = 'general'  # 교양
    GENERAL_ELECTIVE = 'general_elective'  # 일반 선택
    TEACHING = 'teaching'  # 교직
    ALL = 'all'  # 전체

    REQUIREMENT_TYPE = (
        (NONE, 'none'),
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ALL, 'major_all'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching'),
        (ALL, 'all'),
    )

    major = models.ForeignKey(Major, related_name='requirement', on_delete=models.CASCADE)
    start_year = models.PositiveSmallIntegerField(default=2014)
    end_year = models.PositiveSmallIntegerField(default=10000)
    description = models.CharField(max_length=500, blank=True)
    is_credit_requirement = models.BooleanField(default=True)
    required_credit = models.PositiveSmallIntegerField(default=0)
    requirement_type = models.CharField(max_length=50, choices=REQUIREMENT_TYPE)
    is_auto_generated = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        ordering = ['-end_year', '-start_year']


class RequirementChangeHistory(models.Model):
    requirement = models.ForeignKey(Requirement, related_name='requirementchangehistory', on_delete=models.CASCADE)
    entrance_year = models.IntegerField(default=0)
    past_required_credit = models.PositiveIntegerField(default=0)
    curr_required_credit = models.PositiveIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    change_count = models.IntegerField(default=1)


class PlanRequirement(models.Model):
    plan = models.ForeignKey(Plan, related_name='planrequirement', on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, related_name='planrequirement', on_delete=models.CASCADE)
    required_credit = models.PositiveSmallIntegerField(default=0)
#    is_fulfilled = models.BooleanField(default=False)
    earned_credit = models.PositiveSmallIntegerField(default=0)
    auto_calculate = models.BooleanField(default=False)
#    is_updated_by_user = models.BooleanField(default=False)
