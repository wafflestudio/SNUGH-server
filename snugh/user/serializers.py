from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import update_last_login
from core.major.models import Major, UserMajor
from core.major.serializers import MajorSerializer
from user.models import UserProfile
from user.const import STUDENT_STATUS
from core.major.const import *

User = get_user_model()


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


class UserLoginSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    token = serializers.SerializerMethodField()

    def get_token(self, user):
        token, created = Token.objects.get_or_create(user=user)
        return token.key

    def validate(self, data):
        user = authenticate(username=data.pop('email'), password=data.pop('password'))
        if user is None:
            raise PermissionDenied("Username or password wrong")
        update_last_login(None, user)
        self.instance = user
        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='first_name')
    entrance_year = serializers.IntegerField(source='userprofile.entrance_year')
    status = serializers.ChoiceField(choices=STUDENT_STATUS, source='userprofile.status')
    majors = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "password",
            "email",
            "full_name",
            "entrance_year",
            "status",
            "majors",
        )
        read_only_fields = ('id', 'email')
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, user, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                user.set_password(value)
                user.save()
            elif attr == 'userprofile':
                for attr_up, value_up in value.items():
                    setattr(user.userprofile, attr_up, value_up)
                user.userprofile.save()
            else:
                setattr(user, attr, value)
                user.save()
        return user

    def get_majors(self, user):
        majors = Major.objects.filter(usermajor__user=user)
        return MajorSerializer(majors, many=True).data


class UserMajorSerializer(serializers.Serializer):
    major_name = serializers.CharField(required=True, write_only=True)
    major_type = serializers.CharField(required=True, write_only=True)
    majors = serializers.SerializerMethodField()

    def create(self):
        user = self.context.get('request').user
        major = get_object_or_404(Major, **self.validated_data)

        if UserMajor.objects.filter(user=user, major=major).exists():
            raise ValidationError("UserMajor already exists")

        UserMajor.objects.create(user=user, major=major)

        try:
            changed_usermajor = UserMajor.objects.get(user=user, major__major_type=SINGLE_MAJOR)
            not_only_major = changed_usermajor.major
            changed_usermajor.delete()
            new_type_major = Major.objects.get(major_name=not_only_major.major_name, major_type=MAJOR)
            UserMajor.objects.create(user=user, major=new_type_major)
        except UserMajor.DoesNotExist:
            pass

        return MajorSerializer(Major.objects.filter(usermajor__user=user), many=True).data, status.HTTP_201_CREATED

    def delete(self):
        user = self.context.get('request').user
        major = get_object_or_404(Major, **self.validated_data)

        if not UserMajor.objects.filter(user=user, major=major).exists():
            raise NotFound("UserMajor does not exist")

        if len(UserMajor.objects.filter(user=user)) == 1:
            return ValidationError("The number of majors cannot be zero or minus.")

        UserMajor.objects.get(user=user, major=major).delete()

        changed_usermajor = UserMajor.objects.filter(user=user)
        if changed_usermajor.count() == 1:
            only_major = changed_usermajor.first().major
            if only_major.major_type == MAJOR:
                changed_usermajor.first().delete()
                new_type_major = Major.objects.get(major_name=only_major.major_name, major_type=SINGLE_MAJOR)
                UserMajor.objects.create(user=user, major=new_type_major)

        return MajorSerializer(Major.objects.filter(usermajor__user=user), many=True).data, status.HTTP_200_OK

    def get_majors(self, user):
        majors = Major.objects.filter(usermajor__user=self.context.get('request').user)
        return MajorSerializer(majors, many=True).data
