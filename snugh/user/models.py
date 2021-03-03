from django.contrib.auth.models import User
from django.db import models

# UserProfile, Major, UserMajor

class UserProfile(models.Model):
    STUDENT_STATUS = (
        (1, 'active'),# 재학 
        (2, 'inactive'),# 서비스 탈퇴  
        (3, 'break'),# 휴학         
    )
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)
    year = models.IntegerField()
    status = models.PositiveSmallIntegerField(choices=STUDENT_STATUS, default=1)

class Major(models.Model):
    MAJOR_TYPE = (
        (1, 'double_major'),# 복수전공 
        (2, 'minor'),# 부전공 
        (3, 'interdisciplinary_major'),# 연합전공 
        (4, 'interdisciplinary'),# 연계전공 
        (5, 'single_major'),# 단일전공 
        (6, 'interdisciplinary_major_for_teacher_training_programs'),# 교직연합전공 
        (7, 'student_directed_major'),# 학생설계전공 
    )
    major_name = models.CharField(max_length=50, db_index=True)
    major_type = models.PositiveSmallIntegerField(choices=MAJOR_TYPE)

class UserMajor(models.Model):
    user = models.ForeignKey(User, related_name='usermajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='usermajor', on_delete=models.CASCADE)
    class Meta:
        unique_together = (
            ('user', 'major')
        )
