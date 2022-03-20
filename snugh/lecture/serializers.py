from rest_framework import serializers 
from django.db import models
from lecture.models import *
from user.serializers import MajorSerializer

class PlanSerializer(serializers.ModelSerializer):
    majors = serializers.SerializerMethodField()
    semesters = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            'id',
            'user',
            'plan_name',
            'recent_scroll',
            'majors',
            'semesters',
        )
    
    def get_majors(self, plan):
        planmajors = plan.planmajor.select_related('major').all()
        majors = [planmajor.major for planmajor in planmajors]
        return MajorSerializer(majors, many=True).data

    def get_semesters(self, plan):
        semesters = plan.semester.annotate(semester_value=models.Case(
            models.When(semester_type=Semester.FIRST, then=0),
            models.When(semester_type=Semester.SUMMER, then=1),
            models.When(semester_type=Semester.SECOND, then=2),
            models.When(semester_type=Semester.WINTER, then=3),
            output_field=models.IntegerField()
        )).order_by('year', 'semester_value')
        return SemesterSerializer(semesters, many=True).data

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
            'major_requirement_credit',
            'major_elective_credit',
            'general_credit',
            'general_elective_credit',
            'lectures',
        )

    def get_lectures(self, semester):
        semesterlectures = semester.semesterlecture.select_related('lecture', 'recognized_major1', 'recognized_major2').all().order_by('recent_sequence')
        ls = [] 
        for semesterlecture in semesterlectures:
            lecture = semesterlecture.lecture
            ls.append({
                "semesterlecture_id": semesterlecture.id,
                "lecture_id": lecture.id,
                "lecture_code": lecture.lecture_code,
                "lecture_name": lecture.lecture_name,
                "credit": semesterlecture.credit,
                "open_semester": lecture.open_semester,
                "lecture_type": semesterlecture.lecture_type,
                "recognized_major_name1": semesterlecture.recognized_major1.major_name,
                "recognized_major_type1": semesterlecture.recognized_major1.major_type,
                "lecture_type1": semesterlecture.lecture_type1,
                "recognized_major_name2": semesterlecture.recognized_major2.major_name,
                "recognized_major_type2": semesterlecture.recognized_major2.major_type,
                "lecture_type2": semesterlecture.lecture_type2,
                "is_modified": semesterlecture.is_modified,
                "recent_sequence": semesterlecture.recent_sequence
            })
        return ls 


class LectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture 
        fields = '__all__'
    

class SemesterLectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterLecture 
        fields = '__all__'
        