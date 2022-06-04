from django.db import models
from user.const import *
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

     class Meta:
         db_table = 'user'


class UserProfile(models.Model):

    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)
    entrance_year = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=STUDENT_STATUS, default=ACTIVE)
