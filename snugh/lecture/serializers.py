from rest_framework import serializers
from lecture.models import Lecture, SemesterLecture
from lecture.const import *
# TODO: Comments about serializers.

class LectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture 
        fields = '__all__'

class SemesterLectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterLecture 
        fields = '__all__'
