from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BugReport(models.Model):
    """
    Model for bug contents that user reports.
    # TODO: explain fields.
    """
    user = models.ForeignKey(User, related_name='bug_report', on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=300)
    description = models.CharField(max_length=500)
    category = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    