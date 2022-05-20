from django.apps import AppConfig
import os

class LectureConfig(AppConfig):
    name = 'lecture'
    path = os.path.join(settings.BASE_DIR, 'lecture')
