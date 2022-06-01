from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    path = os.path.join(BASE_DIR, 'user')