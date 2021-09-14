from django.db import models
from django.contrib.auth.models import User


class BugReport(models.Model):
    user = models.ForeignKey(User, related_name='bug_report', on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    