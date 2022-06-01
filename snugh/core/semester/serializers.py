from rest_framework import serializers
from core.semester.models import Semester
from snugh.exceptions import DuplicationError, NotOwner
from core.lecture.const import *


class SemesterSerializer(serializers.ModelSerializer):
    lectures = serializers.SerializerMethodField()

    class Meta:
        model = Semester 
        fields = (
            'id', 
            'plan',
            'year',
            'semester_type',
            'major_requirement_credit',
            'major_elective_credit',
            'general_credit',
            'general_elective_credit',
            'lectures',
        )

    def create(self, validated_data):
        plan = validated_data['plan']
        semester_type = validated_data['semester_type']
        year = validated_data['year']
        if plan.user != self.context['request'].user:
            raise NotOwner()
        semester = Semester.objects.filter(plan=plan, semester_type=semester_type, year=year)
        if semester.exists():
            raise DuplicationError("Already exists [Semester]")
        else:
            return Semester.objects.create(plan=plan, semester_type=semester_type, year=year)


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
