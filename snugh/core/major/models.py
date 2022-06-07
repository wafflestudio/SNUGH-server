from django.db import models
from core.major.const import *
from user.models import User


class Major(models.Model):
    """
    Static model related to majors.
        
        # Fields
        major_name (str): Name of major.
        major_type (str): Type of major such as major, single major, double major.
    """
    major_name = models.CharField(max_length=50, db_index=True)
    major_type = models.CharField(max_length=100, choices=MAJOR_TYPE)


class Department(models.Model):
    """
    Static model related to departments.
        
        # Fields
        department_name (str): Name of department.
    """
    department_name = models.CharField(max_length=50, db_index=True)


class MajorDepartment(models.Model):
    """
    Model for relating Major and Department models.
    """
    major = models.ForeignKey(Major, related_name='majordepartment', on_delete=models.CASCADE)
    department = models.ForeignKey(Department, related_name='majordepartment', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('department', 'major')
        )


class DepartmentEquivalent(models.Model):
    """
    Static model related to department which department name equals to major name.
    ex) 간호학과, 경영학과, 약학과, 제약학과(2+4년제), 의예과, 의학과, 자유전공학부
    """
    major_name = models.CharField(max_length=50)
    department_name = models.CharField(max_length=50)


class MajorEquivalent(models.Model):
    """
    Static model related to department which majors split from one major.
    ex) 정치외교학부 외교학과, 디자인학부 디자인과 공예과, 소비자아동학부 소비자학과 아동가족학과
    """
    major_name = models.CharField(max_length=50)
    equivalent_major_name = models.CharField(max_length=50)


class UserMajor(models.Model):
    """
    Model for relating User and Major models.
    """
    user = models.ForeignKey(User, related_name='usermajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='usermajor', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('user', 'major')
        )
