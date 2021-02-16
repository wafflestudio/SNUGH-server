from rest_framework import serializers 
from lecture.models import Plan, Semester, Lecture # PlanMajor, SemesterLecture, MajorLecture 

class PlanSerializer(serializers.ModelSerializer):
    semesters = serializers.SerializerMethodField() 
    class Meta:
        model = Plan
        fields = (
            'id', 
            # 'user_id', 
            'plan_name',
            'recent_scroll',
            'semesters',
        )
    
    def get_semesters(self, plan):
        return SemesterSerializer(plan.semester, many=True).data # plan_id에 해당하는 모든 semester들 

class SemesterSerializer(serializers.ModelSerializer):
    lectures = serializers.SerializerMethodField()
    plan_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Semester 
        fields = (
            'id', 
            'plan',
            'year',
            'semester_type',
            'is_complete',
            'lectures',
            'plan_id'
        )
    
    def create(self, validated_data):
        validated_data['plan'] = Plan.objects.get(id=validated_data.pop('plan_id'))
        return super(SemesterSerializer, self).create(validated_data)

    def get_lectures(self, semester):
        return LectureSerializer(semester.lectures, many=True).data # 해당 semester에 속하는 모든 lecture들, SemesterLecture 

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
