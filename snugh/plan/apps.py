from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class PlanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plan'
    path = os.path.join(BASE_DIR, 'requirement')
    
