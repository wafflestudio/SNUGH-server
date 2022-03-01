from factory.django import DjangoModelFactory

from django.test import TestCase
from django.db import transaction
from rest_framework import status

from django.contrib.auth.models import User
from user.models import UserProfile, Major, UserMajor

class UserFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    email = 'test@test.com'

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
            searched_major = Major.objects.get_or_create(major_name=major['major_name'], major_type=major['major_type'])
            UserMajor.objects.create(user=user, major=searched_major[0])

        userprofile = UserProfile.objects.create(user=user, entrance_year=entrance_year, status=student_status)
        userprofile.save()

        return userprofile

class CreateUserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(
            email='test@test.com',
            password='password',
            entrance_year=2022,
            full_name='홍길동',
            majors=[
                {
                    "major_name": "컴퓨터공학부",
                    "major_type": "major"
                },
                {
                    "major_name": "경영학과",
                    "major_type": "double_major"
                }
            ],
            status='active'
        )

        cls.post_data = {
            'email': 'user@test.com',
            'password': 'password',
            'entrance_year': 2022,
            'full_name': '아무개',
            'majors': [
                {
                    "major_name": "컴퓨터공학부",
                    "major_type": "major"
                },
                {
                    "major_name": "경영학과",
                    "major_type": "double_major"
                }
            ],
            'status': 'active'
        }

    def test_create_user_lacking_requirements(self):
        data = {'email': 'test@test.com'}
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "password, entrance_year, full_name, status, majors missing")

    def test_create_user_wrong_request(self):
        data = self.post_data.copy()
        data.update({'email': 1})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "email wrong_type")

        data = self.post_data.copy()
        data.update({'email': "wrong email"})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "email wrong_format")

        data = self.post_data.copy()
        data.update({'password': "false"})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "password wrong_range(more than 6 letters)")

        data = self.post_data.copy()
        data.update({'entrance_year': 100})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "entrance_year wrong_range(4 digits)")

        data = self.post_data.copy()
        data.update({'full_name': "a"})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "full_name wrong_range(2~30 letters)")

    def test_create_user_email_already_exists(self):
        data = self.post_data.copy()
        data.update({'email': "test@test.com"})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "email already_exist")

    def test_create_user_major_error(self):
        data = self.post_data.copy()
        data.update({'majors': []})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "majors missing")

        data = self.post_data.copy()
        data.update({'majors': [{"major_name": "경영학과", "major_type": "double_major"}]})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "major_type not_allowed")

        data = self.post_data.copy()
        data.update({'majors': [{"major_name": "경영학과", "major_type": "double_major"}, {"major_name": "컴퓨터공학부", "major_type": "double_major"}]})
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "major_type not_allowed")

    def test_create_user(self):
        data = self.post_data
        response = self.client.post('/user/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertIn("id", data)
        self.assertEqual(body["email"], "user@test.com")
        self.assertEqual(body["entrance_year"], 2022)
        self.assertEqual(body["full_name"], "아무개")
        self.assertEqual(body["status"], "active")
        self.assertIn("token", body)

