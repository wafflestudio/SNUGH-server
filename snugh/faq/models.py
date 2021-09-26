from django.db import models


class FAQ(models.Model):
    question = models.CharField(max_length=500)
    answer = models.CharField(max_length=500)
    read_count = models.IntegerField(default=0)
    category = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    