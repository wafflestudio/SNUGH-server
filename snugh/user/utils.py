from factory.django import DjangoModelFactory
from rest_framework.authtoken.models import Token
from faker import Faker

from user.models import UserProfile
from django.contrib.auth import get_user_model
from core.major.models import Major, UserMajor

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    # email = "test@test.com"
    idx = 0

    @classmethod
    def auto_create(cls, **kwargs):
        fake = Faker("ko_KR")
        email = kwargs.get("email", f"test{cls.idx}@snu.ac.kr")

        user = User.objects.create(
            username=email,
            email=email,
            password=kwargs.get("password", fake.password()),
            first_name=kwargs.get("full_name", fake.name())
        )

        UserProfile.objects.create(
            user=user,
            entrance_year=fake.random_choices(
                elements=(2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021), length=1)[0],
            status="active"
        )

        token, created = Token.objects.get_or_create(user=user)

        cls.idx += 1
        return user

    @classmethod
    def create(cls, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')
        entrance_year = kwargs.get('entrance_year')
        full_name = kwargs.get('full_name')
        major_list = kwargs.get('majors')
        student_status = kwargs.get('status')
        user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
        user.set_password(kwargs.get('password', ''))
        user.save()

        for major in major_list:
            searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            UserMajor.objects.create(user=user, major=searched_major)

        userprofile = UserProfile.objects.create(user=user, entrance_year=entrance_year, status=student_status)
        userprofile.save()

        token, created = Token.objects.get_or_create(user=user)

        return user
