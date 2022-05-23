
from django.db import models
from requirement.models import Requirement
from user.models import Major
from lecture.models import Lecture
from lecture.const import *


class BaseChangeHistory(models.Model):
    """
    Abstract base model for LectureTypeChangeHistory & CreditChangeHistory models.
    # TODO: explain fields.
    """
    class Meta:
        abstract = True
    entrance_year = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add = True)
    updated_at = models.DateField(auto_now = True)
    change_count = models.IntegerField(default=0)


class LectureTypeChangeHistory(BaseChangeHistory):
    """
    Model for saving histories of lecture type change in SemesterLecture.
    It wiil be reflected to actual Lecture model's lecture type according to the number of histories.
    # TODO: explain fields.
    """
    major = models.ForeignKey(Major, related_name='lecturetypechangehistory', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='lecturetypechangehistory', on_delete=models.CASCADE)
    past_lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    curr_lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)


class CreditChangeHistory(BaseChangeHistory):
    """
    Model for saving histories of credit change in SemesterLecture.
    It wiil be reflected to actual Lecture model's credit according to the number of histories.
    # TODO: explain fields.
    """
    major = models.ForeignKey(Major, related_name='creditchangehistory', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='creditchangehistory', on_delete=models.CASCADE)
    year_taken = models.IntegerField(default=0)
    past_credit = models.PositiveIntegerField(default=0)
    curr_credit = models.PositiveIntegerField(default=0) 


class RequirementChangeHistory(BaseChangeHistory):
    """
    Model for saving histories of requirement required credit change in PlanRequirement.
    It wiil be reflected to actual Requirement model's required credit according to the number of histories.
    # TODO: explain fields.
    """
    requirement = models.ForeignKey(Requirement, related_name='requirementchangehistory', on_delete=models.CASCADE)
    past_required_credit = models.PositiveIntegerField(default=0)
    curr_required_credit = models.PositiveIntegerField(default=0)
    