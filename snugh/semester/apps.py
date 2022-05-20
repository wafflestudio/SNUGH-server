from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR


class SemesterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'semester'
    path = os.path.join(BASE_DIR, 'semester')
