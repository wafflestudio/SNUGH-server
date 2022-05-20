from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class UserConfig(AppConfig):
    name = 'user'
    path = os.path.join(BASE_DIR, 'user')
