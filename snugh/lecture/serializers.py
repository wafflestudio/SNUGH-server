from rest_framework import serializers 
from lecture.models import Plan, Semester, Lecture 

class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan 
        fields = (
            'id',
            'user_id',
            'plan_name',
            'recent_scroll'
        )

class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Semester 
        fields = (
            'id', 
            'plan_id',
            'year',
            'semester_type',
            'is_complete',
        )

class LectureSerializer(serializers.ModelSerializer):

    class Meta:
        model = Lecture 
        fields = (
            'id', 
            'lecture_name',
            'credit',
            'is_open',
            'open_semester'
        )