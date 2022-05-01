from django.db import models
from user.models import Major
from plan.models import Plan
from requirement.const import *


class Requirement(models.Model):
    """
    Static model related to Graduation Requirements.
    # TODO: explain fields.
    """
    class Meta:
        ordering = ['-end_year', '-start_year']
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


class RequirementChangeHistory(models.Model):
    """
    Model for saving histories of requirement required credit change in PlanRequirement.
    It wiil be reflected to actual Requirement model's required credit according to the number of histories.
    # TODO: explain fields.
    """
    requirement = models.ForeignKey(Requirement, related_name='requirementchangehistory', on_delete=models.CASCADE)
    entrance_year = models.IntegerField(default=0)
    past_required_credit = models.PositiveIntegerField(default=0)
    curr_required_credit = models.PositiveIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    change_count = models.IntegerField(default=0)


class PlanRequirement(models.Model):
    """
    Model for relating Plan and Requirement models. Each plan has requirements based on plan's majors.
    # TODO: explain fields.
    """
    plan = models.ForeignKey(Plan, related_name='planrequirement', on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, related_name='planrequirement', on_delete=models.CASCADE)
    required_credit = models.PositiveSmallIntegerField(default=0)
    earned_credit = models.PositiveSmallIntegerField(default=0)
    auto_calculate = models.BooleanField(default=False)
