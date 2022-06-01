from django.db import models
from core.major.models import Major
from core.lecture.const import *
from core.semester.models import Semester
from core.semester.const import *


class LectureQuerySet(models.QuerySet):
    """Override Queryset of Lecture related model."""
    def search(self, keyword):
        result = self.all()
        for c in keyword:
            result = result.filter(lecture_name__icontains=c)
        return result


class Lecture(models.Model):
    """
    Static model related to lectures.
    # TODO: explain fields.
    """
    lecture_code = models.CharField(max_length=50, default="")
    lecture_name = models.CharField(max_length=50, db_index=True)
    open_department = models.CharField(max_length=50, null=True)
    open_major = models.CharField(max_length=50, null=True)
    open_semester = models.CharField(max_length=50, choices=SEMESTER_TYPE, default=UNKNOWN)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    credit = models.PositiveIntegerField(default=0)
    grade = models.PositiveSmallIntegerField(null=True, blank=True)
    prev_lecture_name = models.CharField(max_length=50, null=True)
    recent_open_year = models.IntegerField(default=0)
    objects = LectureQuerySet.as_manager()


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


class MajorLecture(models.Model):
    """
    Model for relating Major and Lecture models. Each lecture has it's own major.
    Need to created as a static model.
    # TODO: explain fields.
    """
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    is_required = models.BooleanField(default=False)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
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
