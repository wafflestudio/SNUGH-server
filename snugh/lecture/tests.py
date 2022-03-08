from user.utils import UserFactory, UserMajorFactory
from .utils import SemesterFactory, SemesterLectureFactory

from django.test import TestCase
from rest_framework import status

from .models import Plan, PlanMajor, Major, Semester
from requirement.models import PlanRequirement


class PlanTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.auto_create()
        cls.user_token = "Token " + str(cls.user.auth_token)

        cls.post_data = {
            "plan_name": "example plan",
            "majors": [
                {
                    "major_name": "경영학과",
                    "major_type": "double_major"
                },
                {
                    "major_name": "컴퓨터공학부",
                    "major_type": "major"
                }
            ]
        }

        cls.put_data = {
            'email': 'testuser@test.com',
            'password': 'password',
        }

    # POST /plan/

    def test_create_plan_wrong_request(self):
        data = {"plan_name": "example plan"}
        response = self.client.post('/plan/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "majors missing")

        data = self.post_data
        data.update({'majors': [{"major_name": "학부", "major_type": "major"}]})
        response = self.client.post('/plan/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        body = response.json()
        self.assertEqual(body['error'], "major not_exist")

    def test_create_plan(self):
        data = self.post_data
        response = self.client.post('/plan/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        plan = Plan.objects.filter(user=self.user, plan_name="example plan")
        self.assertTrue(plan)
        major = Major.objects.get(major_name="컴퓨터공학부", major_type=Major.MAJOR)
        double_major = Major.objects.get(major_name="경영학과", major_type=Major.DOUBLE_MAJOR)
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=major))
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=double_major))

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["plan_name"], "example plan")
        self.assertIn("recent_scroll", body)
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 2)
        self.assertIn("semesters", body)

        data.update({'plan_name': "single plan"})
        data.update({'majors': [{"major_name": "컴퓨터공학부", "major_type": "major"}]})
        response = self.client.post('/plan/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        plan = Plan.objects.filter(user=self.user, plan_name="single plan")
        self.assertTrue(plan)
        major = Major.objects.get(major_name="컴퓨터공학부", major_type=Major.SINGLE_MAJOR)
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=major))

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["plan_name"], "single plan")
        self.assertIn("recent_scroll", body)
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 1)
        self.assertIn("semesters", body)


class SemesterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.auto_create()
        cls.user_token = "Token " + str(cls.user.auth_token)

        cls.plan = Plan.objects.create(user=cls.user, plan_name="example plan")

        cls.semesters = SemesterFactory(
            semesters=[
                {
                    "plan": cls.plan,
                    "year": 2022,
                    "semester_type": Semester.FIRST
                }
            ]
        )

    def test_create_semester_wrong_input(self):
        data = {"plan": self.plan.id}
        response = self.client.post('/semester/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['error'], "year missing")

        data = {"plan": self.plan.id, "year": 2022, "semester_type": Semester.FIRST}
        response = self.client.post('/semester/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        body = response.json()
        self.assertEqual(body['error'], "semester already_exist")

    def test_create_sememster(self):
        data = {"plan": self.plan.id, "year": 2022, "semester_type": Semester.SECOND}
        response = self.client.post('/semester/', data=data, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["plan"], self.plan.id)
        self.assertEqual(body["year"], 2022)
        self.assertEqual(body["semester_type"], "second")
        self.assertEqual(body["is_complete"], False)
        self.assertEqual(body["major_requirement_credit"], 0)
        self.assertEqual(body["major_elective_credit"], 0)
        self.assertEqual(body["general_credit"], 0)
        self.assertEqual(body["general_elective_credit"], 0)
        self.assertIn("lectures", body)


class LectureTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.auto_create()
        cls.user_token = "Token " + str(cls.user.auth_token)

        cls.plan = Plan.objects.create(user=cls.user, plan_name="example plan")

        cls.semesters = SemesterFactory(
            semesters=[
                {
                    "plan": cls.plan,
                    "year": 2022,
                    "semester_type": Semester.FIRST
                }
            ]
        )


