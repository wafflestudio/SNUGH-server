from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class FAQConfig(AppConfig):
    name = 'faq'
    path = os.path.join(BASE_DIR, 'faq')
