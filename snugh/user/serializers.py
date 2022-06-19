from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from core.major.models import *
from core.major.serializers import MajorSerializer
from user.models import *
from user.const import STUDENT_STATUS
from core.major.const import MAJOR


class UserCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(max_length=100)
    password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    entrance_year = serializers.IntegerField(min_value=1000, max_value=9999, write_only=True)
    full_name = serializers.CharField(max_length=30, min_length=2, write_only=True)
    majors = serializers.ListField(child=serializers.JSONField(), allow_empty=False, write_only=True)
    status = serializers.ChoiceField(choices=STUDENT_STATUS, write_only=True)
    token = serializers.SerializerMethodField()

    def get_token(self, user):
        token, created = Token.objects.get_or_create(user=user)
        return token.key

    def validate_email(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError({'email': "Already existing email."})
        return value

    def validate_major(self, value):
        for major in value:
            if major['major_type'] == MAJOR:
                return value
        raise ValidationError({'majors': "major_type not_allowed"})

    def validate(self, data):
        data['username'] = data.get('email')
        data['first_name'] = data.pop('full_name')
        return data

    def create(self, validated_data):
        entrance_year = validated_data.pop('entrance_year')
        student_status = validated_data.pop('status')
        major_list = validated_data.pop('majors')

        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, entrance_year=entrance_year, status=student_status)

        for major in major_list:
            searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            UserMajor.objects.create(user=user, major=searched_major)

        return user


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
        return user.userprofile.entrance_year

    def get_full_name(self, user):
        return user.first_name

    def get_majors(self, user):
        majors = Major.objects.filter(usermajor__user=user)
        return MajorSerializer(majors, many=True).data

    def get_status(self, user):
        return user.userprofile.status
