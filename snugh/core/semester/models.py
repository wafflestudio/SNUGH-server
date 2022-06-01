from django.db import models
from core.plan.models import Plan
from core.semester.const import *


class Semester(models.Model):
    """
    Model for semester that user makes. User adds lectures in the semester.
    # TODO: explain fields.
    """
    plan = models.ForeignKey(Plan, related_name='semester', on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    semester_type = models.CharField(max_length=50, choices=SEMESTER_TYPE)
    major_requirement_credit = models.PositiveSmallIntegerField(default=0)
    major_elective_credit = models.PositiveSmallIntegerField(default=0)
    general_credit = models.PositiveSmallIntegerField(default=0)
    general_elective_credit = models.PositiveSmallIntegerField(default=0)
