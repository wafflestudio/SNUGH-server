from django.contrib.auth.models import User
from django.db import models
from user.models import Major


# Lecture, Plan, Semester, PlanMajor, SemesterLecture, MajorLecture
class Lecture(models.Model):
    # 공통
    NONE = 'none'  # 구분 없음

    # Semester Type
    UNKNOWN = 'unknown'
    FIRST = 'first'
    SECOND = 'second'
    SUMMER = 'summer'
    WINTER = 'winter'
    ALL = 'all'

    # Lecture Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
    GENERAL = 'general'  # 교양
    GENERAL_ELECTIVE = 'general_elective'  # 일반 선택
    TEACHING = 'teaching'  # 교직

    SEMESTER_TYPE = (
        (UNKNOWN, 'unknown'),
        (FIRST, 'first'),
        (SECOND, 'second'),
        (SUMMER, 'summer'),
        (WINTER, 'winter'),
        (ALL, 'all'),
    )

    LECTURE_TYPE = (
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ELECTIVE, 'major_elective'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching'),
    )

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


class Plan(models.Model):
    user = models.ForeignKey(User, related_name='plan', on_delete=models.CASCADE, default =5)
    plan_name = models.CharField(max_length=50, db_index=True, default="새로운 계획")
    recent_scroll = models.IntegerField(default=0)
    is_first_simulation = models.BooleanField(default = True)


class Semester(models.Model):
    FIRST = 'first'
    SECOND = 'second'
    SUMMER = 'summer'
    WINTER = 'winter'

    SEMESTER_TYPE = (
        (FIRST, 'first'),
        (SECOND, 'second'),
        (SUMMER, 'summer'),
        (WINTER, 'winter'),
    )

    plan = models.ForeignKey(Plan, related_name='semester', on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    semester_type = models.CharField(max_length=50, choices=SEMESTER_TYPE)
    is_complete = models.BooleanField(default=False)
    major_requirement_credit = models.PositiveSmallIntegerField(default=0)
    major_elective_credit = models.PositiveSmallIntegerField(default=0)
    general_credit = models.PositiveSmallIntegerField(default=0)
    general_elective_credit = models.PositiveSmallIntegerField(default=0)


class PlanMajor(models.Model):
    plan = models.ForeignKey(Plan, related_name='planmajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='planmajor', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('plan', 'major')
        )


class SemesterLecture(models.Model):
    # 공통
    NONE = 'none'  # 구분 없음

    # Lecture Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
    GENERAL = 'general'  # 교양
    GENERAL_ELECTIVE = 'general_elective'  # 일반 선택
    TEACHING = 'teaching'  # 교직

    LECTURE_TYPE = (
        (NONE, "none"),
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ELECTIVE, 'major_elective'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching'),
    )

    # Default Major ID
    DEFAULT_MAJOR_ID = 31

    semester = models.ForeignKey(Semester, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    recognized_major1 = models.ForeignKey(Major, related_name='semesterlecture1', on_delete=models.CASCADE, default=DEFAULT_MAJOR_ID)
    lecture_type1 = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    recognized_major2 = models.ForeignKey(Major, related_name='semesterlecture2', on_delete=models.CASCADE, default=DEFAULT_MAJOR_ID)
    lecture_type2 = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)
    recent_sequence = models.PositiveSmallIntegerField()
    is_modified = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('semester', 'lecture')
        )


class MajorLecture(models.Model):
    # 공통
    NONE = 'none'  # 구분 없음

    # Lecture Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
    GENERAL = 'general'  # 교양
    GENERAL_ELECTIVE = 'general_elective'  # 일반 선택
    TEACHING = 'teaching'  # 교직

    LECTURE_TYPE = (
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ELECTIVE, 'major_elective'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching')
    )

    major = models.ForeignKey(Major, related_name='majorlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='majorlecture', on_delete=models.CASCADE)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    is_required = models.BooleanField(default=False)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE, default=NONE)

    # class Meta:
    #     unique_together = (
    #         ('major', 'lecture')
    #     )
