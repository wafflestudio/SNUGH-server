from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class LectureConfig(AppConfig):
    name = 'lecture'
    path = os.path.join(BASE_DIR, 'lecture')
