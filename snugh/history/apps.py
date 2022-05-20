from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class HistoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'history'
    path = os.path.join(BASE_DIR, 'history')
