from rest_framework import serializers
from django.db.models import Case, When, IntegerField, Value
from lecture.models import *
from requirement.models import PlanRequirement
from user.serializers import MajorSerializer
from snugh.exceptions import FieldError, NotFound
from lecture.const import *

class PlanSerializer(serializers.ModelSerializer):
    majors = serializers.SerializerMethodField()
    semesters = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = (
            'id',
            'user',
            'plan_name',
            'majors',
            'semesters',
        )
    
    def get_majors(self, plan):
        planmajors = plan.planmajor.select_related('major').all()
        majors = [planmajor.major for planmajor in planmajors]
        return MajorSerializer(majors, many=True).data

    def get_semesters(self, plan):
        semesters = plan.semester.annotate(semester_value=Case(
            When(semester_type=FIRST, then=Value(0)),
            When(semester_type=SUMMER, then=Value(1)),
            When(semester_type=SECOND, then=Value(2)),
            When(semester_type=WINTER, then=Value(3)),
            output_field=IntegerField()
        )).order_by('year', 'semester_value')
        return SemesterSerializer(semesters, many=True).data

    def create(self, validated_data):
        user = self.context['request'].user
        plan_name = validated_data.get('plan_name', '새로운 계획')
        return Plan.objects.create(user=user, plan_name=plan_name)

class PlanMajorCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanMajor 
        fields = ('plan',)

    def create(self, validated_data):
        majors = validated_data['majors']
        plan = validated_data['plan']
        user = self.context['request'].user
        std = user.userprofile.entrance_year
        planmajors = []
        for major in majors:
            planmajors.append(PlanMajor(plan=plan, major=major))
            requirements = major.requirement.filter(start_year__lte=std, end_year__gte=std)
            planrequirements = []
            for requirement in requirements:
                planrequirements.append(PlanRequirement(plan=plan, 
                                                        requirement=requirement, 
                                                        required_credit=requirement.required_credit))
        PlanRequirement.objects.bulk_create(planrequirements)
        return PlanMajor.objects.bulk_create(planmajors)

    def validate(self, data):
        majors = self.context['request'].data.get('majors')
        if not majors:
            raise FieldError("Field missing [majors]")
        major_instances = []
        for major in majors:
            major_name = major.get('major_name')
            major_type = major.get('major_type')
            if not (major_name and major_type):
                raise FieldError("Field missing [major_name, major_type]")
            try:
                major_instances.append(Major.objects.get(major_name=major_name, major_type=major_type))
            except Major.DoesNotExist:
                raise NotFound("Does not exist [Major]")
        data['majors'] = major_instances
        return data


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
        extra_kwargs = {
            "plan": {"required": True},
            "year": {"required": True},
            "semester_type": {"required": True}}

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
        