from rest_framework import serializers 
from lecture.models import Plan, Semester, Lecture, SemesterLecture 

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

    class Meta:
        model = Semester 
        fields = (
            'id', 
            'plan',
            'year',
            'semester_type',
            'is_complete',
            'lectures',
        )

    def get_lectures(self, semester):
        return LectureSerializer(semester.semesterlecture, many=True).data # 해당 semester에 속하는 모든 lecture들, SemesterLecture 

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

class SemesterLectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterLecture 
        fields = (
            'id', 
            'semester',
            'lecture',
            'lecture_type',
            'lecture_type_detail',
            'lecture_type_detail_detail',
            'recent_sequence', 
        )