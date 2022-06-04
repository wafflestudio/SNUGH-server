from django.test import TestCase
from rest_framework import status
from core.major.models import Major
from user.utils import UserFactory
from user.const import *
from core.major.const import *
from core.plan.models import Plan
from core.plan.utils import plan_major_requirement_generator
from core.semester.const import *
from core.semester.models import Semester
from core.lecture.const import *
from core.lecture.models import Lecture, SemesterLecture
from core.history.models import RequirementChangeHistory
from core.requirement.const import *
from core.requirement.models import PlanRequirement


class RequirementTestCase(TestCase):
    """
    # Test Requirement APIs.
        [GET] requirement/<plan_id>/calculate/
        [PUT] requirement/<plan_id>/
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
                "major_type": "double_major"
            },
            {
                "major_name": "컴퓨터공학부",
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
        cls.major_1 = Major.objects.get(major_name=cls.majors[0]['major_name'], major_type=cls.majors[0]['major_type'])
        cls.major_2 = Major.objects.get(major_name=cls.majors[1]['major_name'], major_type=cls.majors[1]['major_type'])
        cls.major_1_all = cls.plan.planrequirement.get(requirement__major=cls.major_1, requirement__requirement_type=MAJOR_ALL)
        cls.major_1_requirement = cls.plan.planrequirement.get(requirement__major=cls.major_1, requirement__requirement_type=MAJOR_REQUIREMENT)
        cls.major_2_all = cls.plan.planrequirement.get(requirement__major=cls.major_2, requirement__requirement_type=MAJOR_ALL)
        cls.major_2_requirement = cls.plan.planrequirement.get(requirement__major=cls.major_2, requirement__requirement_type=MAJOR_REQUIREMENT)
        cls.all_pr = cls.plan.planrequirement.filter(requirement__requirement_type=ALL).order_by("-required_credit")[0]
        cls.gen_pr = cls.plan.planrequirement.filter(requirement__requirement_type=GENERAL).order_by("-required_credit")[0]

        # 3) create semester.
        cls.semester_1 = Semester.objects.create(
            plan=cls.plan,
            year=2018, 
            semester_type=FIRST,
            major_requirement_credit=6,
            major_elective_credit=6,
            general_credit=3,
            general_elective_credit=3)

        cls.semester_2 = Semester.objects.create(
            plan=cls.plan,
            year=2018, 
            semester_type=SECOND,
            major_requirement_credit=3,
            major_elective_credit=3,
            general_credit=0,
            general_elective_credit=0)

        # 4) create semester lectures.
        # 4-1) create semester_1's major_requirement, major_elective semester lectures.
        cls.lectures_names_1 = [
            "경영과학",
            "마케팅관리",
            "국제경영",
            "고급회계"
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
        cls.lecture_general_elective = Lecture.objects.get(lecture_name="뇌-마음-행동")
        SemesterLecture.objects.create(
            semester=cls.semester_1,
            lecture=cls.lecture_general_elective,
            lecture_type=GENERAL_ELECTIVE,
            lecture_type1=GENERAL_ELECTIVE,
            credit=cls.lecture_general_elective.credit,
            recent_sequence=idx+2
            )

        # 4-3) create semester_2's major_requirement, major_elective semester lectures.
        cls.lectures_names_2 = [
            "알고리즘",
            "인공지능"
        ]
        cls.lectures_2 = Lecture.objects.filter(lecture_name__in=cls.lectures_names_2)
        for idx, lecture in enumerate(list(cls.lectures_2)):
            SemesterLecture.objects.create(
                semester=cls.semester_2,
                lecture=lecture,
                lecture_type=lecture.lecture_type,
                recognized_major1=cls.major_2,
                lecture_type1=lecture.lecture_type,
                credit=lecture.credit,
                recent_sequence=idx
                )
        

    def test_check_requirement(self):
        """
        Test cases in checking plan's requirements.
            1) check plan's requirements.
            2) not plan's owner.
            3) plan does not exist.
        """
        # 1) check plan's requirements.
        response = self.client.get(
            f'/requirement/{self.plan.id}/check/', 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        major_2, major_1 = data['majors']
        major_1_all = self.plan.planrequirement.get(requirement__major=self.major_1, requirement__requirement_type=MAJOR_ALL)
        major_1_requirement = self.plan.planrequirement.get(requirement__major=self.major_1, requirement__requirement_type=MAJOR_REQUIREMENT)
        major_2_all = self.plan.planrequirement.get(requirement__major=self.major_2, requirement__requirement_type=MAJOR_ALL)
        major_2_requirement = self.plan.planrequirement.get(requirement__major=self.major_2, requirement__requirement_type=MAJOR_REQUIREMENT)
        self.assertEqual(major_1['major_name'], self.major_1.major_name)
        self.assertEqual(major_1['major_type'], self.major_1.major_type)
        self.assertEqual(major_1['major_credit'], major_1_all.required_credit)
        self.assertEqual(major_1['major_requirement_credit'], major_1_requirement.required_credit)
        self.assertIn("auto_calculate", major_1)
        self.assertEqual(major_2['major_name'], self.major_2.major_name)
        self.assertEqual(major_2['major_type'], self.major_2.major_type)
        self.assertEqual(major_2['major_credit'], major_2_all.required_credit)
        self.assertEqual(major_2['major_requirement_credit'], major_2_requirement.required_credit)
        self.assertIn("auto_calculate", major_2)
        self.assertEqual(
            data["all"],
            max(self.plan.planrequirement.filter(requirement__requirement_type=ALL).values_list("required_credit", flat=True))
        )
        self.assertEqual(
            data["general"],
            max(self.plan.planrequirement.filter(requirement__requirement_type=GENERAL).values_list("required_credit", flat=True))
        )
        self.assertIn("is_first_simulation", data)
        self.assertIn("is_necessary", data)

        # 2) not plan's owner.
        response = self.client.get(
            f'/requirement/{self.plan.id}/check/', 
            HTTP_AUTHORIZATION=self.stranger_token, 
            content_type="application/json")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3) plan does not exist.
        response = self.client.get(
            '/requirement/9999/check/', 
            HTTP_AUTHORIZATION=self.stranger_token, 
            content_type="application/json")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_calculate_requirement(self):
        """
        Test cases in calculating plan's requirements.
            1) calculate plan's requirements.
            2) not plan's owner.
            3) plan does not exist.
        """
        # 1) calculate plan's requirements.
        response = self.client.get(
            f'/requirement/{self.plan.id}/calculate/', 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        all_progress = data['all_progress']
        major_progress = data['major_progress']
        self.assertEqual(all_progress['all']['required_credit'], 130)
        self.assertEqual(all_progress['all']['earned_credit'], 24)
        self.assertEqual(all_progress['all']['progress'], 0.18)
        self.assertEqual(all_progress['major']['earned_credit'], 18)
        self.assertEqual(all_progress['major']['progress'], 0.23)
        self.assertEqual(all_progress['general']['earned_credit'], 3)
        self.assertEqual(all_progress['general']['progress'], 0.08)
        self.assertEqual(all_progress['other']['earned_credit'], 3)
        self.assertIn(self.majors[0], all_progress['current_planmajors'])
        self.assertIn(self.majors[1], all_progress['current_planmajors'])

        major_1_progress = {
            'major_id': 17, 
            'major_name': '컴퓨터공학부', 
            'major_type': 'major', 
            'major_requirement_credit': {'required_credit': 37, 'earned_credit': 3, 'progress': 0.08}, 
            'major_all_credit': {'required_credit': 41, 'earned_credit': 6, 'progress': 0.15}}
        major_2_progress = {
            'major_id': 335, 
            'major_name': '경영학과', 
            'major_type': 'double_major', 
            'major_requirement_credit': {'required_credit': 30, 'earned_credit': 6, 'progress': 0.2}, 
            'major_all_credit': {'required_credit': 39, 'earned_credit': 12, 'progress': 0.31}}

        self.assertIn(major_1_progress, major_progress)
        self.assertIn(major_2_progress, major_progress)

        # 2) not plan's owner.
        response = self.client.get(
            f'/requirement/{self.plan.id}/check/', 
            HTTP_AUTHORIZATION=self.stranger_token, 
            content_type="application/json")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3) plan does not exist.
        response = self.client.get(
            '/requirement/9999/check/', 
            HTTP_AUTHORIZATION=self.stranger_token, 
            content_type="application/json")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_update_requirement(self):
        """
        Test cases in updating plan's requirements required credits.
            1) change all, general, majors requirement credit.
            2) non-field does not change requirement credit.
            3) non-credit-change does not make requirement history.
            4) not plan's owner.
            5) plan does not exist.
            6) auto_calculate = True.
        """
        major_1_all_credit = self.major_1_all.required_credit
        major_1_requirement_credit = self.major_1_requirement.required_credit
        major_2_all_credit = self.major_2_all.required_credit
        major_2_requirement_credit = self.major_2_requirement.required_credit
        all_credit = self.all_pr.required_credit
        all_requirement = self.all_pr.requirement
        general_credit = self.gen_pr.required_credit
        general_requirement = self.gen_pr.requirement
        body = {
            "majors": [
                {
                    "major_name": "경영학과",
                    "major_type": "double_major",
                    "major_credit": 40,
                    "major_requirement_credit": 33,
                    "auto_calculate": False
                },
                {
                    "major_name": "컴퓨터공학부",
                    "major_type": "major",
                    "major_credit": 45,
                    "major_requirement_credit": 31,
                    "auto_calculate": False
                }
            ],
            "all": 135,
            "general": 40
        }
        response = self.client.put(
            f'/requirement/{self.plan.id}/', 
            HTTP_AUTHORIZATION=self.user_token,
            data=body,
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(body, data)
        self.major_1_all.refresh_from_db()
        self.assertEqual(
            True,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_1_all.requirement,
                past_required_credit=major_1_all_credit,
                curr_required_credit=40,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.major_1_requirement.refresh_from_db()
        self.assertEqual(
            True,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_1_requirement.requirement,
                past_required_credit=major_1_requirement_credit,
                curr_required_credit=33,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.major_2_all.refresh_from_db()
        self.assertEqual(
            True,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_2_all.requirement,
                past_required_credit=major_2_all_credit,
                curr_required_credit=45,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.major_2_requirement.refresh_from_db()
        self.assertEqual(
            True,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_2_requirement.requirement,
                past_required_credit=major_2_requirement_credit,
                curr_required_credit=31,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.all_pr.refresh_from_db()
        self.assertEqual(
            True,
            RequirementChangeHistory.objects.filter(
                requirement=all_requirement,
                past_required_credit=all_credit,
                curr_required_credit=135,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.gen_pr.refresh_from_db()
        self.assertEqual(
            True,
            RequirementChangeHistory.objects.filter(
                requirement=general_requirement,
                past_required_credit=general_credit,
                curr_required_credit=40,
                change_count=1,
                entrance_year=2018
            ).exists()
        )

        # 2) non-field does not change requirement credit.
        major_1_all_credit = self.major_1_all.required_credit
        major_1_requirement_credit = self.major_1_requirement.required_credit
        major_2_all_credit = self.major_2_all.required_credit
        major_2_requirement_credit = self.major_2_requirement.required_credit
        all_credit = self.all_pr.required_credit
        general_credit = self.gen_pr.required_credit
        empty_body = {}
        response = self.client.put(
            f'/requirement/{self.plan.id}/', 
            HTTP_AUTHORIZATION=self.user_token,
            data=empty_body,
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        major_1_all = self.plan.planrequirement.get(requirement__major=self.major_1, requirement__requirement_type=MAJOR_ALL)
        major_1_requirement = self.plan.planrequirement.get(requirement__major=self.major_1, requirement__requirement_type=MAJOR_REQUIREMENT)
        major_2_all = self.plan.planrequirement.get(requirement__major=self.major_2, requirement__requirement_type=MAJOR_ALL)
        major_2_requirement = self.plan.planrequirement.get(requirement__major=self.major_2, requirement__requirement_type=MAJOR_REQUIREMENT)
        all_pr = self.plan.planrequirement.filter(requirement__requirement_type=ALL).order_by("-required_credit")[0]
        gen_pr = self.plan.planrequirement.filter(requirement__requirement_type=GENERAL).order_by("-required_credit")[0]
        self.assertEqual(body, data)
        self.assertEqual(major_1_all_credit, major_1_all.required_credit)
        self.assertEqual(major_1_requirement_credit, major_1_requirement.required_credit)
        self.assertEqual(major_2_all_credit, major_2_all.required_credit)
        self.assertEqual(major_2_requirement_credit, major_2_requirement.required_credit)
        self.assertEqual(all_credit, all_pr.required_credit)
        self.assertEqual(general_credit, gen_pr.required_credit)

        # 3) non-credit-change does not make requirement history.
        response = self.client.put(
            f'/requirement/{self.plan.id}/', 
            HTTP_AUTHORIZATION=self.user_token,
            data=body,
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(body, data)
        self.major_1_all.refresh_from_db()
        self.assertEqual(
            False,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_1_all.requirement,
                past_required_credit=self.major_1_all.required_credit,
                curr_required_credit=self.major_1_all.required_credit,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.major_1_requirement.refresh_from_db()
        self.assertEqual(
            False,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_1_requirement.requirement,
                past_required_credit=self.major_1_requirement.required_credit,
                curr_required_credit=self.major_1_requirement.required_credit,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.major_2_all.refresh_from_db()
        self.assertEqual(
            False,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_2_all.requirement,
                past_required_credit=self.major_2_all.required_credit,
                curr_required_credit=self.major_2_all.required_credit,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.major_2_requirement.refresh_from_db()
        self.assertEqual(
            False,
            RequirementChangeHistory.objects.filter(
                requirement=self.major_2_requirement.requirement,
                past_required_credit=self.major_2_requirement.required_credit,
                curr_required_credit=self.major_2_requirement.required_credit,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.all_pr.refresh_from_db()
        self.assertEqual(
            False,
            RequirementChangeHistory.objects.filter(
                requirement=all_requirement,
                past_required_credit=135,
                curr_required_credit=135,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
        self.gen_pr.refresh_from_db()
        self.assertEqual(
            False,
            RequirementChangeHistory.objects.filter(
                requirement=general_requirement,
                past_required_credit=40,
                curr_required_credit=40,
                change_count=1,
                entrance_year=2018
            ).exists()
        )
    
        # 4) not plan's owner.
        response = self.client.put(
            f'/requirement/{self.plan.id}/', 
            HTTP_AUTHORIZATION=self.stranger_token,
            data=body,
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 5) plan does not exist.
        response = self.client.put(
            '/requirement/9999/', 
            HTTP_AUTHORIZATION=self.user_token,
            data=body,
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 6) auto_calculate = True.
        body = {
            "majors": [
                {
                    "major_name": "경영학과",
                    "major_type": "double_major",
                    "auto_calculate": True
                },
                {
                    "major_name": "컴퓨터공학부",
                    "major_type": "major",
                    "auto_calculate": True
                }
            ],
        }
        response = self.client.put(
            f'/requirement/{self.plan.id}/', 
            HTTP_AUTHORIZATION=self.user_token,
            data=body,
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        result = {
            'majors': 
                [{
                    'major_type': 'double_major', 
                    'major_credit': 40, 
                    'major_requirement_credit': 64, 
                    'auto_calculate': True, 
                    'major_name': '경영학과'}, 
                {
                    'major_type': 'major', 
                    'major_credit': 45, 
                    'major_requirement_credit': 49, 
                    'auto_calculate': True, 
                    'major_name': '컴퓨터공학부'}], 
            'all': 135, 
            'general': 40}
        self.assertEqual(data, result)
