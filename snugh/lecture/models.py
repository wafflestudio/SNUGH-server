from django.db import models
from django.contrib.auth.models import User
from user.models import Major
from lecture.const import *


class LectureQuerySet(models.QuerySet):
    """Override Queryset of Lecture related model."""
    def search(self, keyword):
        result = self.all()
        for c in keyword:
            result = result.filter(lecture_name__icontains=c)
        return result


class BaseLecture(models.Model):
    """
    Abstract base model for Lecture & LectureTmp models.
    # TODO: explain fields.
    """
    class Meta:
        abstract = True
    lecture_code = models.CharField(max_length=50, default="")
    lecture_name = models.CharField(max_length=50, db_index=True)
    open_department = models.CharField(max_length=50, null=True)
    open_major = models.CharField(max_length=50, null=True)
    open_semester = models.CharField(max_length=50, choices=SEMESTER_TYPE, default=UNKNOWN)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    credit = models.PositiveIntegerField(default=0)
    grade = models.PositiveSmallIntegerField(null=True, blank=True)


class BaseMajorLecture(models.Model):
    """
    Abstract base model for MajorLecture & MajorLectureTmp models.
    # TODO: explain fields.
    """
    class Meta:
        abstract = True
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    is_required = models.BooleanField(default=False)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)


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


class Lecture(BaseLecture):
    """
    Static model related to lectures.
    # TODO: explain fields.
    """
    prev_lecture_name = models.CharField(max_length=50, null=True)
    recent_open_year = models.IntegerField(default=0)
    objects = LectureQuerySet.as_manager()
    

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


class Plan(models.Model):
    """
    Model for plan that user makes. User adds semesters and lectures in the plan.
    # TODO: explain fields.
    """
    user = models.ForeignKey(User, related_name='plan', on_delete=models.CASCADE, default=5)
    plan_name = models.CharField(max_length=50, db_index=True, default="새로운 계획")
    is_first_simulation = models.BooleanField(default = True)


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


class PlanMajor(models.Model):
    """
    Model for relating Plan and Major models. Each plan has user-selected majors.
    # TODO: explain fields.
    """
    plan = models.ForeignKey(Plan, related_name='planmajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='planmajor', on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'major'],
                name='major already exists in plan.'
            )
        ]


class SemesterLecture(models.Model):
    """
    Model for relating Semester and Lecture models. Each semester has user-selected lectures.
    # TODO: explain fields.
    """
    semester = models.ForeignKey(Semester, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    recognized_major1 = models.ForeignKey(Major, related_name='semesterlecture1', on_delete=models.CASCADE, default=DEFAULT_MAJOR_ID)
    lecture_type1 = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    recognized_major2 = models.ForeignKey(Major, related_name='semesterlecture2', on_delete=models.CASCADE, default=DEFAULT_MAJOR_ID)
    lecture_type2 = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    credit = models.PositiveIntegerField(default=0)
    recent_sequence = models.PositiveSmallIntegerField()
    is_modified = models.BooleanField(default=False)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['semester', 'lecture'],
                name='lecture already exists in semester.'
            )
        ]


class MajorLecture(BaseMajorLecture):
    """
    Model for relating Major and Lecture models. Each lecture has it's own major.
    Need to created as a static model.
    # TODO: explain fields.
    """
    major = models.ForeignKey(Major, related_name='majorlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='majorlecture', on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)


class LectureCredit(models.Model):
    """
    Model for relating Lecture and Credit models. Each lecture has it's own credit.
    # TODO: explain fields.
    """
    lecture = models.ForeignKey(Lecture, related_name='lecturecredit', on_delete=models.CASCADE)
    credit = models.PositiveIntegerField(default=0)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)


class LectureTmp(BaseLecture):
    """
    # TODO: Comments about this model.
    """
    open_year = models.IntegerField(default=0)
    is_added =  models.BooleanField(default=False)


class MajorLectureTmp(BaseMajorLecture):
    """
    # TODO: Comments about this model.
    """
    major_name = models.CharField(max_length=50, default="")
    major_type = models.CharField(max_length=50, default="")
    lecture_code = models.CharField(max_length=50, default="")
