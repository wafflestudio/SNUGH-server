from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class RequirementConfig(AppConfig):
    name = 'requirement'
    path = os.path.join(BASE_DIR, 'requirement')
