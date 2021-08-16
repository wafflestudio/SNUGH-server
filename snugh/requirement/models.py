from django.db import models
from user.models import Major
from lecture.models import Plan


# Requirement, PlanRequirement
class Requirement(models.Model):
    # 공통
    NONE = 'none'  # 구분 없음

    # Requirement Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
    GENERAL = 'general'  # 교양
    GENERAL_ELECTIVE = 'general_elective'  # 일반 선택
    TEACHING = 'teaching'  # 교직
    ALL = 'all'  # 전체

    REQUIREMENT_TYPE = (
        (NONE, 'none'),
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ELECTIVE, 'major_elective'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching'),
        (ALL, 'all'),
    )

    major = models.ForeignKey(Major, related_name='requirement', on_delete=models.CASCADE)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=500, blank=True)
    is_credit_requirement = models.BooleanField()
    required_credit = models.PositiveSmallIntegerField(default=0)
    requirement_type = models.CharField(max_length=50, choices=REQUIREMENT_TYPE)

    class Meta:
        ordering = ['-end_year', '-start_year']  # 최신순


class PlanRequirement(models.Model):
    plan = models.ForeignKey(Plan, related_name='planrequirement', on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, related_name='planrequirement', on_delete=models.CASCADE)
    required_credit = models.PositiveSmallIntegerField(default=0)
    is_fulfilled = models.BooleanField(default=False)
    earned_credit = models.PositiveSmallIntegerField(default=0)
    auto_calculate = models.BooleanField(default=False)
