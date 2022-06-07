from factory.django import DjangoModelFactory
from core.major.models import UserMajor


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
