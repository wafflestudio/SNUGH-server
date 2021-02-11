from django.contrib.auth.models import User 
from django.db import models

# Create your models here.

class Plan(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=50, blank=True)
    recent_scroll = models.IntegerField() 
