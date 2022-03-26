from user.utils import UserFactory, UserMajorFactory
from lecture.utils import SemesterFactory, SemesterLectureFactory

from django.test import TestCase
from rest_framework import status

from lecture.models import Plan, PlanMajor, Major, Semester, Lecture, SemesterLecture
from .models import Requirement, PlanRequirement


class RequirementTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.auto_create()
        cls.user_token = "Token " + str(cls.user.auth_token)

        majors = [
            {
                "major_name": "경영학과",
                "major_type": "double_major"
            },
            {
                "major_name": "컴퓨터공학부",
                "major_type": "major"
            }
        ]
        cls.post_data = {
            "plan_name": "example plan",
            "majors": majors
        }

        cls.plan = Plan.objects.create(user=cls.user, plan_name="example plan")

        cls.semester = Semester.objects.create(plan=cls.plan, year=2021, semester_type=Semester.SECOND)

        for major in majors:
            searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            PlanMajor.objects.create(plan=cls.plan, major=searched_major)

        for major in majors:
            searched_major = Major.objects.get(major_name=major['major_name'], major_type=major['major_type'])
            requirements = Requirement.objects.filter(major=searched_major,
                                                      start_year__lte=cls.user.userprofile.entrance_year,
                                                      end_year__gte=cls.user.userprofile.entrance_year)
            for requirement in requirements:
                PlanRequirement.objects.create(plan=cls.plan, requirement=requirement,
                                               required_credit=requirement.required_credit)

        lecture_id_list = [364, 365, 401, 403, 433, 434]
        recognized_major_name_list = ["컴퓨터공학부", "컴퓨터공학부", "컴퓨터공학부", "컴퓨터공학부", "경영학과", "경영학과"]

        for i in range(len(lecture_id_list)):
            lecture_id = lecture_id_list[i]
            lecture = Lecture.objects.get(id=lecture_id)
            lecture_type = lecture.lecture_type
            recognized_major_name = recognized_major_name_list[i]

            if lecture_type in [Lecture.MAJOR_REQUIREMENT, Lecture.MAJOR_ELECTIVE, Lecture.TEACHING]:
                if PlanMajor.objects.filter(plan=cls.plan, major__major_name=recognized_major_name).exists():
                    recognized_major = Major.objects.get(planmajor__plan=cls.plan, major_name=recognized_major_name)
                else:
                    recognized_major = Major.objects.get(id=Major.DEFAULT_MAJOR_ID)
                    lecture_type = Lecture.GENERAL_ELECTIVE
            else:
                recognized_major = Major.objects.get(id=Major.DEFAULT_MAJOR_ID)

            semlecture = SemesterLecture.objects.create(semester=cls.semester,
                                                        lecture=lecture,
                                                        lecture_type=lecture_type,
                                                        recognized_major1=recognized_major,
                                                        lecture_type1=lecture_type,
                                                        credit=lecture.credit,
                                                        recent_sequence=len(lecture_id_list)+i)
            semlecture.save()

            if lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
                cls.semester.major_requirement_credit += lecture.credit
                cls.semester.save()
            elif lecture_type == SemesterLecture.MAJOR_ELECTIVE or lecture_type == SemesterLecture.TEACHING:
                cls.semester.major_elective_credit += lecture.credit
                cls.semester.save()
            elif lecture_type == SemesterLecture.GENERAL:
                cls.semester.general_credit += lecture.credit
                cls.semester.save()
            elif lecture_type == SemesterLecture.GENERAL_ELECTIVE:
                cls.semester.general_elective_credit += lecture.credit
                cls.semester.save()

    # GET /requirement/

    def test_list_requirement_wrong_request(self):
        plan_id = str(self.plan.id + 1)
        response = self.client.get('/requirement/?plan_id=' + plan_id, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_requirement(self):
        plan_id = str(self.plan.id)
        response = self.client.get('/requirement/?plan_id=' + plan_id, HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        all_progress = body['all_progress']
        major_progress = body['major_progress']
        self.assertEqual(all_progress['all']['required_credit'], 130)
        self.assertEqual(all_progress['all']['earned_credit'], 18)
        self.assertEqual(all_progress['major']['earned_credit'], 18)
        self.assertEqual(all_progress['general']['earned_credit'], 0)
        self.assertEqual(all_progress['other']['earned_credit'], 0)
        self.assertEqual(len(all_progress['current_planmajors']), 2)
        self.assertEqual(major_progress[0]['major_id'], 17)
        self.assertEqual(major_progress[1]['major_id'], 335)

    # GET /requirement/{plan_id}/loading/

    def test_retrieve_requirement_wrong_request(self):
        plan_id = str(self.plan.id + 1)
        response = self.client.get('/requirement/' + plan_id + '/loading/', HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_requirement(self):
        plan_id = str(self.plan.id)
        response = self.client.get('/requirement/' + plan_id + '/loading/', HTTP_AUTHORIZATION=self.user_token, content_type="application/json")
        self.assertTrue(Plan.objects.filter(id=plan_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(len(body["majors"]), 2)
        self.assertIn("major_name", body["majors"][0])
        self.assertIn("major_type", body["majors"][0])
        self.assertIn("major_credit", body["majors"][0])
        self.assertIn("major_requirement_credit", body["majors"][0])
        self.assertIn("auto_calculate", body["majors"][0])
        self.assertIn("all", body)
        self.assertIn("general", body)
        self.assertIn("is_first_simulation", body)
        self.assertIn("is_necessary", body)

