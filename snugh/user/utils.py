from factory.django import DjangoModelFactory
from faker import Faker
from .models import User, UserMajor, UserProfile
from rest_framework.authtoken.models import Token

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    #email = "test@test.com"
    idx = 0

    @classmethod
    def create(cls, **kwargs):

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

class UserMajorFactory(DjangoModelFactory):
    class Meta:
        model = UserMajor

    @classmethod
    def create(cls, **kwargs):

        user = kwargs.get("user", None)
        majors = kwargs.get("majors", None)
        
        if user and majors:

            usermajors = [UserMajor(user=user, major=major) for major in majors]
            return UserMajor.objects.bulk_create(usermajors)
        
        return None