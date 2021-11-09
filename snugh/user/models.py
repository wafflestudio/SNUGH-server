from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    BREAK = 'break'

    STUDENT_STATUS = (
        (ACTIVE, 'active'),  # 재학
        (INACTIVE, 'inactive'),  # 서비스 탈퇴
        (BREAK, 'break'),  # 휴학
    )

    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)
    entrance_year = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STUDENT_STATUS, default=ACTIVE)


class Major(models.Model):
    MAJOR = 'major'
    DOUBLE_MAJOR = 'double_major'
    MINOR = 'minor'
    INTERDISCIPLINARY_MAJOR = 'interdisciplinary_major'
    INTERDISCIPLINARY = 'interdisciplinary'
    SINGLE_MAJOR = 'single_major'
    INTERDISCIPLINARY_MAJOR_FOR_TEACHER = 'interdisciplinary_major_for_teacher'
    STUDENT_DIRECTED_MAJOR = 'student_directed_major'
    INTERDISCIPLINARY_PROGRAM = 'interdisciplinary_program'

    MAJOR_TYPE = (
        (MAJOR, 'major'),
        (DOUBLE_MAJOR, 'double_major'),  # 복수전공
        (MINOR, 'minor'),  # 부전공
        (INTERDISCIPLINARY_MAJOR, 'interdisciplinary_major'),  # 연합전공
        (INTERDISCIPLINARY, 'interdisciplinary'),  # 연계전공
        (SINGLE_MAJOR, 'single_major'),  # 단일전공
        (INTERDISCIPLINARY_MAJOR_FOR_TEACHER, 'interdisciplinary_major_for_teacher'),  # 교직연합전공
        (STUDENT_DIRECTED_MAJOR, 'student_directed_major'),  # 학생설계전공
        (INTERDISCIPLINARY_PROGRAM, 'interdisciplinary_program'),  # 협동과정
    )

    # TODO: Modify Default Major ID from 31 to 0
    DEFAULT_MAJOR_ID = 31

    DEFAULT_MAJOR_NAME = 'none'
    DEFAULT_MAJOR_TYPE = 'major'

    major_name = models.CharField(max_length=50, db_index=True)
    major_type = models.CharField(max_length=100, choices=MAJOR_TYPE)

class Department(models.Model):
    department_name = models.CharField(max_length=50, db_index=True)

class MajorDepartment(models.Model):
    major = models.ForeignKey(Major, related_name='majordepartment', on_delete=models.CASCADE)
    department = models.ForeignKey(Department, related_name='majordepartment', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('department', 'major')
        )

class UserMajor(models.Model):
    user = models.ForeignKey(User, related_name='usermajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='usermajor', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('user', 'major')
        )
