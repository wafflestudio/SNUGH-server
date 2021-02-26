from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from user.models import *

class UserSerializer(serializers.ModelSerializer):
    id= serializers.IntegerField()
    username= serializers.CharField()
    first_name= serializers.CharField()
    last_name= serializers.CharField()
    full_name= serializers.SerializerMethodField()
    student_id= serializers.SerializerMethodField()
    major=serializers.SerializerMethodField()
    status=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=(
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "student_id",
            "status",
            "major"
        )

    def get_student_id(self, user):
        userprofile=user.userprofile
        return userprofile.student_id

    def get_status(self, user):
        userprofile=user.userprofile
        return userprofile.status

    def get_major(self, user):
        ls=[]
        usermajors=user.usermajor.all()
        for usermajor in usermajors:
            body={"id":usermajor.major.id, "name":usermajor.major.major_name, "type":usermajor.major.major_type}
            ls.append(body)
        return ls

    def get_full_name(self, user):
        return user.first_name+user.last_name


