from django.contrib.auth.models import User 
from django.db import models

# Create your models here.

class Plan(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=50, blank=True)
    recent_scroll = models.IntegerField() 

class Semester(models.Model):
    UNKNOWN = 'unknown'
    FIRST = 'first'
    SECOND = 'second'
    SUMMER = 'summer'
    WINTER = 'winter' 

    SEMESTER_TYPE = (
        (UNKNOWN, UNKNOWN),
        (FIRST, FIRST),
        (SECOND, SECOND),
        (SUMMER, SUMMER),
        (WINTER, WINTER),
    )
    
    TYPES = (UNKNOWN, FIRST, SECOND, SUMMER, WINTER) 

    semester_type = models.CharField(max_length=10, choices=SEMESTER_TYPE, default=UNKNOWN)
    plan_id = models.ForeignKey(Plan, on_delete=models.CASCADE)
    year = models.IntegerField()
    is_complete = models.BooleanField() 

class Lecture(models.Model):
    UNKNOWN = 'unknown'
    FIRST = 'first'
    SECOND = 'second'
    SUMMER = 'summer'
    WINTER = 'winter' 

    SEMESTER_TYPE = (
        (UNKNOWN, UNKNOWN),
        (FIRST, FIRST),
        (SECOND, SECOND),
        (SUMMER, SUMMER),
        (WINTER, WINTER),
    )
    
    TYPES = (UNKNOWN, FIRST, SECOND, SUMMER, WINTER) 

    open_semester = models.CharField(max_length=10, choices=SEMESTER_TYPE, default=UNKNOWN)
    lecture_name = models.CharField(max_length=50, blank=True)
    credit = models.IntegerField() 
    is_open = models.BooleanField()
