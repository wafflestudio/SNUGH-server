from django.apps import AppConfig
import os
from snugh.settings.base import BASE_DIR

class BugReportConfig(AppConfig):
    name = 'bug_report'
    path = os.path.join(BASE_DIR, 'bug_report')
