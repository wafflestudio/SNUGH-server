from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from user.models import *

class UserSerializer(serializers.ModelSerializer):
    id= serializers.IntegerField()
    username= serializers.CharField()
    first_name= serializers.CharField()
    last_name= serializers.CharField()
    student_id= serializers.SerializerMethodField()
#    cumulative_semester = serializers.SerializerMethodField()
    major=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=(
            "id",
            "username",
            "first_name",
            "last_name",
            "student_id",
#            "cumulative_semester"
            "major"
        )
        
    def get_student_id(self, user):
        userprofile=user.userprofile
        return userprofile.student_id

    def get_major(self, user):
        ls=[]
        usermajors=user.usermajor.all()
        for usermajor in usermajors:
            body={"id":usermajor.major.id, "name":usermajor.major.major_name, "type":usermajor.major.major_type}
            ls.append(body)
        return ls


#    def get_cumulative_semester(self, user):
#        userprofile=user.userprofile
#        return userprofile.cumulative_semester


"""
userConfig
status

cumulative semester
status
pk와other query params 관련 """
