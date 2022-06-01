from django.test import TestCase
from rest_framework import status
from core.major.models import Major
from user.utils import UserFactory
from core.major.const import *
from core.plan.models import Plan, PlanMajor
from core.plan.utils import plan_major_requirement_generator
from core.semester.models import Semester
from core.semester.const import *
from core.lecture.models import Lecture, SemesterLecture
from core.lecture.utils_test import SemesterLectureFactory
from core.requirement.models import PlanRequirement
from core.const import *
from user.const import *

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
        self.assertTrue(plan.exists())
        major = Major.objects.get(major_name="컴퓨터공학부", major_type=MAJOR)
        double_major = Major.objects.get(major_name="경영학과", major_type=DOUBLE_MAJOR)
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=major).exists())
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=double_major).exists())
        self.assertTrue(PlanRequirement.objects.filter(
            plan=plan[0], 
            requirement__major=major,
            requirement__start_year__lte=self.user.userprofile.entrance_year,
            requirement__end_year__gte=self.user.userprofile.entrance_year).exists())
        self.assertTrue(PlanRequirement.objects.filter(
            plan=plan[0], 
            requirement__major=double_major,
            requirement__start_year__lte=self.user.userprofile.entrance_year,
            requirement__end_year__gte=self.user.userprofile.entrance_year).exists())

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
        self.assertTrue(plan.exists())
        major = Major.objects.get(major_name="컴퓨터공학부", major_type=SINGLE_MAJOR)
        self.assertTrue(PlanMajor.objects.filter(plan=plan[0], major=major).exists())
        self.assertTrue(PlanRequirement.objects.filter(
            plan=plan[0], 
            requirement__major=major,
            requirement__start_year__lte=self.user.userprofile.entrance_year,
            requirement__end_year__gte=self.user.userprofile.entrance_year).exists())

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

    
    def test_delete_plan(self):
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

    
    def test_update_plan(self):
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
            "/plan/9999/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_retrieve_plan(self):
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
            "/plan/9999/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        

class PlanMajorCopyTestCase(TestCase):
    """
    # Test Plan APIs.
        [POST] plan/<plan_id>/copy/
        [PUT] plan/<plan_id>/major/
    """

    @classmethod
    def setUpTestData(cls):
        """
            1) create plan.
            2) create plan major & plan requirement.
            3) create semester.
            4) create semester lectures.
        """

        # 1) create plan.
        cls.majors = [
            {
                "major_name": "경영학과",
                "major_type": "major"
            }
        ]
        cls.user = UserFactory.create(
            email = "jaejae2374@test.com",
            password = "waffle1234",
            entrance_year = 2018,
            full_name = "test user",
            majors = cls.majors,
            status = ACTIVE
        )
        cls.user_token = "Token " + str(cls.user.auth_token)
        cls.stranger = UserFactory.auto_create()
        cls.stranger_token = "Token " + str(cls.stranger.auth_token)
        
        cls.plan = Plan.objects.create(user=cls.user, plan_name="plan example")

        # 2) create plan major & plan requirement.
        plan_major_requirement_generator(cls.plan, cls.majors, 2018)
        cls.major_1 = Major.objects.get(major_name="경영학과", major_type="major")
        cls.major_2 = Major.objects.get(major_name="컴퓨터공학부", major_type="major")

        # 3) create semester.
        cls.semester_1 = Semester.objects.create(
            plan=cls.plan,
            year=2018, 
            semester_type=FIRST,
            major_requirement_credit=3,
            major_elective_credit=3,
            general_credit=3,
            general_elective_credit=3)

        cls.semester_2 = Semester.objects.create(
            plan=cls.plan,
            year=2018, 
            semester_type=SECOND,
            major_requirement_credit=3,
            major_elective_credit=3,
            general_credit=0,
            general_elective_credit=6)

        # 4) create semester lectures.
        # 4-1) create semester_1's major_requirement, major_elective semester lectures.
        cls.lectures_names_1 = [
            "경영과학",
            "고급회계",
        ]
        cls.lectures_1 = Lecture.objects.filter(lecture_name__in=cls.lectures_names_1)
        for idx, lecture in enumerate(list(cls.lectures_1)):
            SemesterLecture.objects.create(
                semester=cls.semester_1,
                lecture=lecture,
                lecture_type=lecture.lecture_type,
                recognized_major1=cls.major_1,
                lecture_type1=lecture.lecture_type,
                credit=lecture.credit,
                recent_sequence=idx
                )

        # 4-2) create semester_1's general, general_elective semester lectures.
        cls.lecture_general = Lecture.objects.get(lecture_name="법과 문학")
        SemesterLecture.objects.create(
            semester=cls.semester_1,
            lecture=cls.lecture_general,
            lecture_type=cls.lecture_general.lecture_type,
            lecture_type1=cls.lecture_general.lecture_type,
            credit=cls.lecture_general.credit,
            recent_sequence=idx+1
            )
        cls.lecture_general_elective_1 = Lecture.objects.get(lecture_name="알고리즘")
        SemesterLecture.objects.create(
            semester=cls.semester_1,
            lecture=cls.lecture_general_elective_1,
            lecture_type=GENERAL_ELECTIVE,
            lecture_type1=GENERAL_ELECTIVE,
            credit=cls.lecture_general_elective_1.credit,
            recent_sequence=idx+2
            )

        # 4-3) create semester_2's major_requirement, major_elective semester lectures.
        cls.lectures_names_2 = [
            "마케팅관리",
            "국제경영"
        ]
        cls.lectures_2 = Lecture.objects.filter(lecture_name__in=cls.lectures_names_2)
        for idx, lecture in enumerate(list(cls.lectures_2)):
            SemesterLecture.objects.create(
                semester=cls.semester_2,
                lecture=lecture,
                lecture_type=lecture.lecture_type,
                recognized_major1=cls.major_1,
                lecture_type1=lecture.lecture_type,
                credit=lecture.credit,
                recent_sequence=idx
                )

        # 4-2) create semester_2's general elective semester lectures.
        cls.lecture_general_elective_2 = Lecture.objects.get(lecture_name="뇌-마음-행동")
        SemesterLecture.objects.create(
            semester=cls.semester_2,
            lecture=cls.lecture_general_elective_2,
            lecture_type=GENERAL_ELECTIVE,
            lecture_type1=GENERAL_ELECTIVE,
            credit=cls.lecture_general_elective_2.credit,
            recent_sequence=idx+1
            )
        cls.lecture_general_elective_3 = Lecture.objects.get(lecture_name="인공지능")
        SemesterLecture.objects.create(
            semester=cls.semester_2,
            lecture=cls.lecture_general_elective_3,
            lecture_type=GENERAL_ELECTIVE,
            lecture_type1=GENERAL_ELECTIVE,
            credit=cls.lecture_general_elective_3.credit,
            recent_sequence=idx+2
            )

    
    def test_major_update(self):
        """
        Test cases in updating plan's major.
            1) update plan's major.
            2) not plan's owner.
            3) not found.
        """
        # 1) update plan's major.
        response = self.client.put(
            f"/plan/{self.plan.id}/major/",
            data={
                "majors": [
                    {
                        "major_name": "컴퓨터공학부",
                        "major_type": "major"
                    }
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.plan.id)
        self.assertEqual(data['plan_name'], "plan example")
        self.assertEqual(data['majors'][0]['major_name'], "컴퓨터공학부")
        self.assertEqual(data['majors'][0]['major_type'], "major")
        self.assertFalse(self.plan.planmajor.filter(
            plan=self.plan,
            major=self.major_1
        ).exists())
        self.assertTrue(self.plan.planmajor.filter(
            plan=self.plan,
            major=self.major_2
        ).exists())
        self.assertFalse(self.plan.planrequirement.filter(
            plan=self.plan, 
            requirement__major=self.major_1,
            requirement__start_year__lte=self.user.userprofile.entrance_year,
            requirement__end_year__gte=self.user.userprofile.entrance_year
        ).exists())
        self.assertTrue(self.plan.planrequirement.filter(
            plan=self.plan, 
            requirement__major=self.major_2,
            requirement__start_year__lte=self.user.userprofile.entrance_year,
            requirement__end_year__gte=self.user.userprofile.entrance_year
        ).exists())
        
        self.assertEqual(
            self.semester_1.semesterlecture.get(
                lecture=self.lectures_1.get(lecture_name="경영과학")
            ).lecture_type,
            GENERAL_ELECTIVE
        )
        self.assertEqual(
            self.semester_1.semesterlecture.get(
                lecture=self.lectures_1.get(lecture_name="고급회계")
            ).lecture_type,
            GENERAL_ELECTIVE
        )
        self.assertEqual(
            self.semester_1.semesterlecture.get(
                lecture=self.lecture_general_elective_1
            ).lecture_type,
            MAJOR_REQUIREMENT
        )
        self.assertEqual(
            self.semester_1.semesterlecture.get(
                lecture=self.lecture_general
            ).lecture_type,
            GENERAL
        )
        self.semester_1.refresh_from_db()
        self.assertEqual(self.semester_1.major_requirement_credit, 3)
        self.assertEqual(self.semester_1.major_elective_credit, 0)
        self.assertEqual(self.semester_1.general_credit, 3)
        self.assertEqual(self.semester_1.general_elective_credit, 6)

        self.assertEqual(
            self.semester_2.semesterlecture.get(
                lecture=self.lectures_2.get(lecture_name="국제경영")
            ).lecture_type,
            MAJOR_ELECTIVE
        )
        self.assertEqual(
            self.semester_2.semesterlecture.get(
                lecture=self.lectures_2.get(lecture_name="마케팅관리")
            ).lecture_type,
            MAJOR_ELECTIVE
        )
        self.assertEqual(
            self.semester_2.semesterlecture.get(
                lecture=self.lecture_general_elective_2
            ).lecture_type,
            GENERAL_ELECTIVE
        )
        self.assertEqual(
            self.semester_2.semesterlecture.get(
                lecture=self.lecture_general_elective_3
            ).lecture_type,
            MAJOR_ELECTIVE
        )
        self.semester_2.refresh_from_db()
        self.assertEqual(self.semester_2.major_requirement_credit, 0)
        self.assertEqual(self.semester_2.major_elective_credit, 9)
        self.assertEqual(self.semester_2.general_credit, 0)
        self.assertEqual(self.semester_2.general_elective_credit, 3)

        # 2) not plan's owner.
        response = self.client.put(
            f"/plan/{self.plan.id}/major/",
            data={
                "majors": [
                    {
                        "major_name": "컴퓨터공학부",
                        "major_type": "major"
                    }
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3) not found.
        response = self.client.put(
            "/plan/9999/major/",
            data={
                "majors": [
                    {
                        "major_name": "컴퓨터공학부",
                        "major_type": "major"
                    }
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    

    def test_copy_plan(self):
        """
        Test cases in copying plan.
            1) copy plan.
            2) not plan's owner.
            3) not found.
        """
        # 1) copy plan.
        response = self.client.post(
            f"/plan/{self.plan.id}/copy/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertNotEqual(data['id'], self.plan.id)
        self.assertEqual(data['plan_name'], "plan example (복사본)")
        self.assertEqual(data['majors'][0]['major_name'], "경영학과")
        self.assertEqual(data['majors'][0]['major_type'], "major")

        new_plan = Plan.objects.get(id=data['id'])

        self.assertTrue(new_plan.planmajor.filter(major=self.major_1).exists())
        self.assertTrue(new_plan.planrequirement.filter(
            requirement__major=self.major_1,
            requirement__start_year__lte=self.user.userprofile.entrance_year,
            requirement__end_year__gte=self.user.userprofile.entrance_year
        ).exists())
        new_semester_1 = new_plan.semester.filter(
            year=self.semester_1.year,
            semester_type=self.semester_1.semester_type,
            major_requirement_credit=self.semester_1.major_requirement_credit,
            major_elective_credit=self.semester_1.major_elective_credit,
            general_credit=self.semester_1.general_credit,
            general_elective_credit=self.semester_1.general_elective_credit,
        )
        self.assertTrue(new_semester_1.exists())
        new_semester_2 = new_plan.semester.filter(
            year=self.semester_2.year,
            semester_type=self.semester_2.semester_type,
            major_requirement_credit=self.semester_2.major_requirement_credit,
            major_elective_credit=self.semester_2.major_elective_credit,
            general_credit=self.semester_2.general_credit,
            general_elective_credit=self.semester_2.general_elective_credit,
        )
        self.assertTrue(new_semester_2.exists())
        semesterlectures_1 = [
            "경영과학",
            "고급회계",
            "법과 문학",
            "알고리즘"
        ]
        for lecture_name in semesterlectures_1:
            self.assertTrue(new_semester_1[0].semesterlecture.filter(
            lecture__lecture_name=lecture_name
            ).exists())

        semesterlectures_2 = [
            "마케팅관리",
            "국제경영",
            "뇌-마음-행동",
            "인공지능"
        ]
        for lecture_name in semesterlectures_2:
            self.assertTrue(new_semester_2[0].semesterlecture.filter(
            lecture__lecture_name=lecture_name
            ).exists())

        # 2) not plan's owner.
        response = self.client.post(
            f"/plan/{self.plan.id}/copy/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3) not found.
        response = self.client.post(
            "/plan/9999/copy/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
