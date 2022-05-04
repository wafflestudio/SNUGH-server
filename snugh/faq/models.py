from django.db import models
from user.models import User


class FAQ(models.Model):
    """
    Model for FAQ from users.
    # TODO: explain fields.
    """
    question = models.CharField(max_length=500)
    answer = models.CharField(max_length=500, blank=True)
    category = models.CharField(max_length=50, null=True)
    read_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    