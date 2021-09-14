from rest_framework import serializers 
from bug_report.models import BugReport


class BugReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BugReport
        fields = '__all__'
