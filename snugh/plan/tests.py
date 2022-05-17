from django.test import TestCase
from rest_framework import status
from user.utils import UserFactory
from user.const import *
from plan.models import Plan, PlanMajor
from user.models import Major
from semester.models import Semester
from lecture.models import Lecture
from lecture.utils_test import SemesterLectureFactory


class PlanTestCase(TestCase):
    """
    # Test Plan APIs.
        [POST] plan/
        [GET] plan/
        [GET] plan/<plan_id>/
        [DELETE] plan/<plan_id>/
        [PUT] plan/<plan_id>/
    """

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory.auto_create()
        cls.user_token = "Token " + str(cls.user.auth_token)
        cls.stranger = UserFactory.auto_create()
        cls.stranger_token = "Token " + str(cls.stranger.auth_token)

        cls.major_1 = Major.objects.get(major_name="경영학과", major_type="single_major")
        cls.major_2 = Major.objects.get(major_name="컴퓨터공학부", major_type="single_major")


    def test_create_plan_errors(self):
        """
        Error cases in creating plan.
            1) majors field missing.
            2) major_name, major_type field missing in majors.
            3) majors not found.
            4) majors already exists.
        """
        # 1) majors field missing.
        data = {"plan_name": "example plan"}
        response = self.client.post(
            '/plan/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['detail'], "Field missing [majors]")

        # 2) major_name, major_type field missing in majors.
        data = {
            "plan_name": "example plan",
            "majors": [
                {
                    "major_name": "경영학과",
                }
            ]
        }
        response = self.client.post(
            '/plan/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json"
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['detail'], "Field missing [major_name, major_type]")

        data = {
            "plan_name": "example plan",
            "majors": [
                {
                    "major_type": "major",
                }
            ]
        }
        response = self.client.post(
            '/plan/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json"
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['detail'], "Field missing [major_name, major_type]")

        # 3) majors not found.
        data = {
            "plan_name": "example plan",
            "majors": [
                {
                    "major_name": "샤프심학과",
                    "major_type": "major"
                }
            ]
        }
        response = self.client.post(
            '/plan/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json"
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        body = response.json()
        self.assertEqual(body['detail'], "Does not exist [Major]")

        # 4) majors already exists.
        data = {
            "plan_name": "example plan",
            "majors": [
                {
                    "major_name": "경영학과",
                    "major_type": "major"
                },
                {
                    "major_name": "경영학과",
                    "major_type": "major"
                }
            ]
        }
        response = self.client.post(
            '/plan/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json"
            )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        body = response.json()
        self.assertEqual(body['detail'], "Already exists [PlanMajor]")


    def test_create_plan(self):
        """
        Test cases in creating plan.
            1) plan with double majors.
            2) plan with single major.
        """
        # 1) plan with double majors.
        data = {
            "plan_name": "plan with double major",
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
        response = self.client.post(
            '/plan/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        plan = Plan.objects.filter(user=self.user, plan_name="plan with double major")
        self.assertTrue(plan)
        major = Major.objects.get(major_name="컴퓨터공학부", major_type=MAJOR)
        double_major = Major.objects.get(major_name="경영학과", major_type=DOUBLE_MAJOR)
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=major))
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=double_major))

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["plan_name"], "plan with double major")
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 2)

        # 2) plan with single major.
        data = {
            "plan_name": "plan with single major",
            "majors": [
                {
                    "major_name": "컴퓨터공학부",
                    "major_type": "single_major"
                }
            ]
        } 
        response = self.client.post(
            '/plan/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        plan = Plan.objects.filter(user=self.user, plan_name="plan with single major")
        self.assertTrue(plan)
        major = Major.objects.get(major_name="컴퓨터공학부", major_type=SINGLE_MAJOR)
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=major))

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["plan_name"], "plan with single major")
        self.assertIn("majors", body)
        self.assertEqual(len(body["majors"]), 1)


    def test_plan_list(self):
        """
        Test cases in listing plan.
        """
        p1 = Plan.objects.create(user=self.user, plan_name="example plan 1")
        p2 = Plan.objects.create(user=self.user, plan_name="example plan 2")
        PlanMajor.objects.create(major=self.major_1, plan=p1)
        PlanMajor.objects.create(major=self.major_2, plan=p2)

        response = self.client.get(
            "/plan/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        plan_1 = data[0]
        self.assertEqual(plan_1['plan_name'], p1.plan_name)
        self.assertEqual(len(plan_1['majors']), 1)
        self.assertEqual(plan_1['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(plan_1['majors'][0]['major_type'], self.major_1.major_type)

        plan_2 = data[1]
        self.assertEqual(plan_2['plan_name'], p2.plan_name)
        self.assertEqual(len(plan_2['majors']), 1)
        self.assertEqual(plan_2['majors'][0]['major_name'], self.major_2.major_name)
        self.assertEqual(plan_2['majors'][0]['major_type'], self.major_2.major_type)

    
    def test_plan_delete(self):
        """
        Test cases in deleting plan.
            1) not plan's owner.
            2) delete plan.
        """
        plan = Plan.objects.create(user=self.user, plan_name="example plan")
        # 1) not plan's owner.
        response = self.client.delete(
            f"/plan/{plan.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2) delete plan.
        response = self.client.delete(
            f"/plan/{plan.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.user.plan.filter(plan_name="example plan").exists(), False)

    
    def test_plan_update(self):
        """
        Test cases in updating plan's name.
            1) not plan's owner.
            2) update plan name.
            3) not found.
        """
        plan = Plan.objects.create(user=self.user, plan_name="example plan")

        # 1) not plan's owner.
        response = self.client.put(
            f"/plan/{plan.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2) update plan name.
        response = self.client.put(
            f"/plan/{plan.id}/",
            data={
                "plan_name": "example plan modified"
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        plan.refresh_from_db()
        self.assertEqual(data['plan_name'], "example plan modified")
        self.assertEqual(plan.plan_name, "example plan modified")

        # 3) not found.
        response = self.client.put(
            f"/plan/9999/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_plan_retrieve(self):
        """
        Test cases in retrieving plan's name.
            1) retrieve plan.
            2) not found.
        """
        plan = Plan.objects.create(user=self.user, plan_name="plan example")
        PlanMajor.objects.create(major=self.major_1, plan=plan)
        semester_1 = Semester.objects.create(plan=plan, year=2016, semester_type="first")
        semester_2 = Semester.objects.create(plan=plan, year=2016, semester_type="second")
        lecture_examples = [
            "경영과학",
            "회계원리",
            "고급회계",
        ]
        lectures = Lecture.objects.filter(lecture_name__in=lecture_examples)
        SemesterLectureFactory.create(
            semester=semester_1,
            lectures=lectures,
            recognized_majors=[self.major_1]*3
        )

        # 1) retrieve plan.
        response = self.client.get(
            f"/plan/{plan.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['plan_name'], "plan example")
        self.assertEqual(len(data['majors']), 1)
        self.assertEqual(data['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(data['majors'][0]['major_type'], self.major_1.major_type)
        
        self.assertEqual(len(data['semesters']), 2)
        self.assertEqual(data['semesters'][0]['year'], semester_1.year)
        self.assertEqual(data['semesters'][0]['semester_type'], semester_1.semester_type)
        self.assertEqual(len(data['semesters'][0]['lectures']), 3)

        self.assertEqual(data['semesters'][1]['year'], semester_2.year)
        self.assertEqual(data['semesters'][1]['semester_type'], semester_2.semester_type)
        self.assertEqual(len(data['semesters'][1]['lectures']), 0)

        # 2) not found.
        response = self.client.get(
            f"/plan/9999/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        