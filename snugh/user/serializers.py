from rest_framework import serializers
from django.contrib.auth.models import User
from user.models import Major


class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    email = serializers.CharField()
    entrance_year = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    majors = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "entrance_year",
            "full_name",
            "majors",
            "status",
        )

    def get_entrance_year(self, user):
        userprofile = user.userprofile
        return userprofile.entrance_year

    def get_full_name(self, user):
        return user.first_name

    def get_majors(self, user):
        majors = Major.objects.filter(usermajor__user=user)
        return MajorSerializer(majors, many=True).data

    def get_status(self, user):
        userprofile = user.userprofile
        return userprofile.status


class MajorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    major_name = serializers.CharField()
    major_type = serializers.CharField()

    class Meta:
        model = Major
        fields = (
            "id",
            "major_name",
            "major_type",
        )