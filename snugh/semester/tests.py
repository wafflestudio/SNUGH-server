from django.test import TestCase
from lecture.models import Lecture
from lecture.utils_test import SemesterLectureFactory
from user.utils import UserFactory
from plan.models import Plan, PlanMajor
from rest_framework import status
from semester.models import Semester
from user.models import Major

class SemesterTestCase(TestCase):
    """
    # Test Semester APIs.
        [GET] semester/<semester_id>/
        [DELETE] semester/<semester_id>/
    """
    
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.auto_create()
        cls.user_token = "Token " + str(cls.user.auth_token)
        cls.stranger = UserFactory.auto_create()
        cls.stranger_token = "Token " + str(cls.stranger.auth_token)
        
        cls.plan = Plan.objects.create(user=cls.user, plan_name="example plan")
        cls.major = Major.objects.get(major_name="경영학과", major_type="single_major")
        PlanMajor.objects.create(
            major=cls.major, 
            plan=cls.plan)


    def test_create_semester_errors(self):
        """
        Error cases in creating semester.
            1) fields missing.
            2) not plan's owner.
            3) semester already exists.
        """
        # 1) fields missing. [semester_type]
        data = {
            "plan": self.plan.id,
            "year": 2016
        }
        response = self.client.post(
            '/semester/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 1) fields missing. [year]
        data = {
            "plan": self.plan.id,
            "semester_type": "first"
        }
        response = self.client.post(
            '/semester/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 1) fields missing. [plan]
        data = {
            "year": 2016,
            "semester_type": "first"
        }
        response = self.client.post(
            '/semester/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 2) not plan's owner.
        data = {
            "plan": self.plan.id,
            "year": 2016,
            "semester_type": "first"
        }
        response = self.client.post(
            '/semester/', 
            data=data, 
            HTTP_AUTHORIZATION=self.stranger_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        body = response.json()
        self.assertEqual(body['detail'], "권한이 없습니다.")

        # 3) semester already exists.
        Semester.objects.create(
            plan=self.plan,
            year=2016,
            semester_type="first"
        )
        data = {
            "plan": self.plan.id, 
            "year": 2016, 
            "semester_type": "first"
        }
        response = self.client.post(
            '/semester/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        body = response.json()
        self.assertEqual(body['detail'], "Already exists [Semester]")


    def test_create_sememster(self):
        """
        Test cases in creating semester.
        """
        data = {
            "plan": self.plan.id, 
            "year": 2016, 
            "semester_type": "second"
        }
        response = self.client.post(
            '/semester/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()

        self.assertIn("id", body)
        self.assertEqual(body["plan"], self.plan.id)
        self.assertEqual(body["year"], 2016)
        self.assertEqual(body["semester_type"], "second")
        self.assertEqual(body["major_requirement_credit"], 0)
        self.assertEqual(body["major_elective_credit"], 0)
        self.assertEqual(body["general_credit"], 0)
        self.assertEqual(body["general_elective_credit"], 0)
        self.assertIn("lectures", body)


    def test_semester_delete(self):
        """
        Test cases in deleting semester.
            1) not semester's owner.
            2) delete semester.
        """
        semester = Semester.objects.create(
            plan=self.plan,
            year=2017,
            semester_type="first"
        )
        # 1) not semester's owner.
        response = self.client.delete(
            f"/semester/{semester.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2) delete semester.
        response = self.client.delete(
            f"/semester/{semester.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Semester.objects.filter(plan=self.plan, year=2017, semester_type='first').exists(), False)


    def test_semester_retrieve(self):
        """
        Test cases in retrieving semester.
            1) retrieve semester.
            2) not found.
        """
        semester = Semester.objects.create(
            plan=self.plan,
            year=2017,
            semester_type="first"
        )
        lecture_examples = [
            "경영과학",
            "회계원리",
            "고급회계",
        ]
        lectures = Lecture.objects.filter(lecture_name__in=lecture_examples)
        SemesterLectureFactory.create(
            semester=semester,
            lectures=lectures,
            recognized_majors=[self.major]*3
        )

        # 1) retrieve semester.
        response = self.client.get(
            f"/semester/{semester.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['id'], semester.id)
        self.assertEqual(data['plan'], self.plan.id)
        self.assertEqual(data['year'], semester.year)
        self.assertEqual(data['semester_type'], semester.semester_type)
        self.assertIn('major_requirement_credit', data)
        self.assertIn('major_elective_credit', data)
        self.assertIn('general_credit', data)
        self.assertIn('general_elective_credit', data)
        self.assertEqual(len(data['lectures']), 3)

        # 2) not found.
        response = self.client.get(
            "/semester/9999/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)