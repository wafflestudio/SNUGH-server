from rest_framework import serializers 
from lecture.models import *


class PlanSerializer(serializers.ModelSerializer):
    majors = serializers.SerializerMethodField()
    semesters = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            'id',
            'plan_name',
            'recent_scroll',
            'majors',
            'semesters',
        )
    
    def get_majors(self, plan):
        planmajors = PlanMajor.objects.filter(plan=plan)
        ls = [] 
        for planmajor in planmajors:
            ls.append({
                "id": planmajor.major.id, 
                "major_name": planmajor.major.major_name,
                "major_type": planmajor.major.major_type,
            })
        return ls 

    def get_semesters(self, plan):
        semesters = plan.semester.all().order_by('year', 'semester_type')
        return SemesterSerializer(semesters, many=True).data # plan_id에 해당하는 모든 semester들


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
        semesterlectures = SemesterLecture.objects.filter(semester=semester).order_by('recent_sequence')
        ls = [] 
        for semesterlecture in semesterlectures:
            lecture = semesterlecture.lecture
            ls.append({
                "semesterlecture_id": semesterlecture.id,
                "lecture_id": lecture.id,
                "lecture_code": lecture.lecture_code,
                "lecture_name": lecture.lecture_name,
                "credit": lecture.credit, 
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
        