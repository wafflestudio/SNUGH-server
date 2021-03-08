from rest_framework import serializers 
from lecture.models import Plan, Semester, Lecture, SemesterLecture 

class PlanSerializer(serializers.ModelSerializer):
    semesters = serializers.SerializerMethodField() 
    class Meta:
        model = Plan
        fields = (
            'id', 
            'user', 
            'plan_name',
            'recent_scroll',
            'semesters',
        )
    
    def get_semesters(self, plan):
        return SemesterSerializer(plan.semester, many=True).data # plan_id에 해당하는 모든 semester들 

class SimpleSemesterSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Semester 
        fields = '__all__'

class SemesterSerializer(serializers.ModelSerializer):
    lectures = serializers.SerializerMethodField()
    major_requirement_credits = serializers.SerializerMethodField() 
    major_elective_credits = serializers.SerializerMethodField() 
    general_credits = serializers.SerializerMethodField() 

    class Meta:
        model = Semester 
        fields = (
            'id', 
            'plan',
            'year',
            'semester_type',
            'is_complete',
            'major_requirement_credits',
            'major_elective_credits',
            'general_credits',
            'lectures',
        )

    def get_lectures(self, semester):
        semesterlectures = semester.semesterlecture.all() 
        ls = [] 
        for semesterlecture in semesterlectures:
            lecture = semesterlecture.lecture
            ls.append({
                "lecture_id": lecture.id, 
                "semesterlecture_id": semesterlecture.id, 
                "lecture_name": lecture.lecture_name,
                "credit": lecture.credit, 
                "is_open": lecture.is_open, 
                "open_semester": lecture.open_semester, 
            })
        return ls 

    def get_major_requirement_credits(self, semester):
        total_credits = 0
        semesterlectures = semester.semesterlecture.all() 
        for semesterlecture in semesterlectures: 
            if semesterlecture.lecture_type == 2:
                total_credits += semesterlecture.lecture.credit 
        return total_credits 

    def get_major_elective_credits(self, semester):
        total_credits = 0
        semesterlectures = semester.semesterlecture.all() 
        for semesterlecture in semesterlectures: 
            if semesterlecture.lecture_type == 3:
                total_credits += semesterlecture.lecture.credit 
        return total_credits 

    def get_general_credits(self, semester): 
        total_credits = 0
        semesterlectures = semester.semesterlecture.all() 
        for semesterlecture in semesterlectures: 
            if semesterlecture.lecture_type == 1:
                total_credits += semesterlecture.lecture.credit 
        return total_credits 

class LectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture 
        fields = '__all__'
    
class SemesterLectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterLecture 
        fields = '__all__'