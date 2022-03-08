from .utils import UserTestFactory

from django.test import TestCase
from rest_framework import status


class UserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserTestFactory(
            email='testuser@test.com',
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

        cls.user_token = "Token " + str(cls.user.auth_token)

        cls.post_data = {
            'email': 'member@test.com',
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

        cls.put_data = {
            'email': 'testuser@test.com',
            'password': 'password',
        }

    # POST /user/

    def test_create_user_missing_requirements(self):
        data = {'email': 'test@test.com'}
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "password, entrance_year, full_name, status, majors missing")

    def test_create_user_wrong_request(self):
        data = self.post_data.copy()
        data.update({'email': 1})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "email wrong_type")

        data = self.post_data.copy()
        data.update({'email': "wrong email"})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "email wrong_format")

        data = self.post_data.copy()
        data.update({'password': "false"})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "password wrong_range(more than 6 letters)")

        data = self.post_data.copy()
        data.update({'entrance_year': 100})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "entrance_year wrong_range(4 digits)")

        data = self.post_data.copy()
        data.update({'full_name': "a"})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "full_name wrong_range(2~30 letters)")

    def test_create_user_email_already_exists(self):
        data = self.post_data.copy()
        data.update({'email': "testuser@test.com"})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "email already_exist")

    def test_create_user_major_error(self):
        data = self.post_data.copy()
        data.update({'majors': []})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "majors missing")

        data = self.post_data.copy()
        data.update({'majors': [{"major_name": "경영학과", "major_type": "double_major"}]})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "major_type not_allowed")

        data = self.post_data.copy()
        data.update({'majors': [{"major_name": "경영학과", "major_type": "double_major"}, {"major_name": "컴퓨터공학부", "major_type": "double_major"}]})
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "major_type not_allowed")

    def test_create_user(self):
        data = self.post_data
        response = self.client.post('/user/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["email"], "member@test.com")
        self.assertEqual(body["entrance_year"], 2022)
        self.assertEqual(body["full_name"], "아무개")
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 2)
        self.assertEqual(body["status"], "active")
        self.assertIn("token", body)

    # PUT /user/login/

    def test_login_missing_requirements(self):
        data = {'email': 'member@test.com'}
        response = self.client.put('/user/login/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "password missing")

    def test_login_wrong_request(self):
        data = self.put_data.copy()
        data.update({'password': "false"})
        response = self.client.put('/user/login/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        body = response.json()
        self.assertEqual(body['error'], "username or password wrong")

    def test_login(self):
        data = self.put_data
        response = self.client.put('/user/login/', data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["email"], "testuser@test.com")
        self.assertEqual(body["entrance_year"], 2022)
        self.assertEqual(body["full_name"], "홍길동")
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 2)
        self.assertEqual(body["status"], "active")
        self.assertIn("token", body)

    # GET /user/logout/

    def test_logout(self):
        response = self.client.get('/user/logout/', HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_me(self):
        response = self.client.get('/user/me/', HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["email"], "testuser@test.com")
        self.assertEqual(body["entrance_year"], 2022)
        self.assertEqual(body["full_name"], "홍길동")
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 2)
        self.assertEqual(body["status"], "active")

    def test_update_me(self):
        data = {'entrance_year': 2021}
        response = self.client.put('/user/me/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["email"], "testuser@test.com")
        self.assertEqual(body["entrance_year"], 2021)
        self.assertEqual(body["full_name"], "홍길동")
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 2)
        self.assertEqual(body["status"], "active")
