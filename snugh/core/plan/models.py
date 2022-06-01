from django.db import models
from core.major.models import Major
from django.contrib.auth import get_user_model

User = get_user_model()


class Plan(models.Model):
    """
    Model for plan that user makes. User adds semesters and lectures in the plan.
    # TODO: explain fields.
    """
    user = models.ForeignKey(User, related_name='plan', on_delete=models.CASCADE, default=5)
    plan_name = models.CharField(max_length=50, db_index=True, default="새로운 계획")
    is_first_simulation = models.BooleanField(default = True)


class PlanMajor(models.Model):
    """
    Model for relating Plan and Major models. Each plan has user-selected majors.
    # TODO: explain fields.
    """
    plan = models.ForeignKey(Plan, related_name='planmajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='planmajor', on_delete=models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'major'],
                name='major already exists in plan.'
            )
        ]
