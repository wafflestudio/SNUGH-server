from rest_framework import serializers 
from bug_report.models import BugReport
from snugh.exceptions import FieldError


class BugReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BugReport
        fields = '__all__'
        extra_kwargs = {
            "title": {"required": True},
            "description": {"required": True}}
    

    def validate(self, data):
        title = data['title']
        description = data['description']
        if len(title) < 5:
            raise FieldError("Invalid field [credit]")
        if len(description) < 10:
            raise FieldError("Invalid field [description]")
        return data
        

    def create(self, validated_data):
        return BugReport.objects.create(
            user=self.context['request'].user, 
            title=self.validated_data['title'], 
            description=self.validated_data['description'], 
            category=self.validated_data.get('category'))
