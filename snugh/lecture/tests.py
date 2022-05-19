from django.test import TestCase
from rest_framework import status
from user.utils import UserFactory

from user.models import Major
from lecture.models import Lecture, SemesterLecture
from plan.models import Plan, PlanMajor
from semester.models import Semester
from history.models import CreditChangeHistory, LectureTypeChangeHistory
from user.const import *
from semester.const import *

class LectureTestCase(TestCase):
    """
    # Test Lecture APIs.
        [POST] lecture/
        [GET] lecture/
        [DELETE] lecture/<semesterlecture_id>/
    """

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory.create(
            email = "jaejae2374@test.com",
            password = "waffle1234",
            entrance_year = 2018,
            full_name = "test user",
            majors = [{
                "major_name":"경영학과",
                "major_type":"major"
            }],
            status = ACTIVE
        )
        cls.user_token = "Token " + str(cls.user.auth_token)
        cls.stranger = UserFactory.auto_create()
        cls.stranger_token = "Token " + str(cls.stranger.auth_token)
        
        cls.plan = Plan.objects.create(user=cls.user, plan_name="plan example")

        cls.semester_1 = Semester.objects.create(plan=cls.plan, year=2018, semester_type=FIRST)
        cls.semester_2 = Semester.objects.create(
            plan=cls.plan,
            year=2018, 
            semester_type=SECOND,
            major_requirement_credit=6,
            major_elective_credit=3)
        
        cls.major = Major.objects.get(major_name="경영학과", major_type="single_major")
        cls.planmajor = PlanMajor.objects.create(major=cls.major, plan=cls.plan)
        cls.lecture_examples = [
            "경영과학", 
            "알고리즘", 
            "고급회계",
            "공급사슬관리",
            "국제경영"
        ]
        cls.lectures = Lecture.objects.filter(lecture_name__in=cls.lecture_examples)
        cls.lectures_id = list(Lecture.objects.filter(lecture_name__in=cls.lecture_examples).values_list(flat=True))

        cls.existing_lectures_name = [
            "경영학원론", 
            "마케팅사례연구",
            "마케팅관리"
        ]
        cls.existing_lectures = Lecture.objects.filter(lecture_name__in=cls.existing_lectures_name)
        for idx, lecture in enumerate(list(cls.existing_lectures)):
            SemesterLecture.objects.create(
                semester=cls.semester_2,
                lecture=lecture,
                lecture_type=lecture.lecture_type,
                recognized_major1=cls.major,
                lecture_type1=lecture.lecture_type,
                credit=lecture.credit,
                recent_sequence=idx
                )
        

    def test_create_lecture_errors(self):
        """
        Error cases in creating semester lecture.
            1) not semester's owner.
            2) semester does not exist.
            3) lecture already exists in plan.
        """
        # 1) not semester's owner.
        data = {
            "semester_id": self.semester_1.id,
            "lecture_id": self.lectures_id
        }
        response = self.client.post(
            '/lecture/', 
            data=data, 
            HTTP_AUTHORIZATION=self.stranger_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2) semester does not exist.
        data = {
            "semester_id": 9999,
            "lecture_id": self.lectures_id
        }
        response = self.client.post(
            '/lecture/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        body = response.json()
        self.assertEqual(body['detail'], "semester does not exist")


    def test_create_lecture(self):
        """
        Test cases in creating semester lecture.
            1) create semester lecture.
            2) lecture already exists in plan.
        """
        # 1) create semester lecture.
        data = {
            "semester_id": self.semester_1.id,
            "lecture_id": self.lectures_id
        }
        response = self.client.post(
            '/lecture/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["plan"], self.plan.id)
        self.assertEqual(body["year"], 2018)
        self.assertEqual(body["semester_type"], FIRST)
        self.assertEqual(body["major_requirement_credit"], 3)
        self.assertEqual(body["major_elective_credit"], 9)
        self.assertEqual(body["general_credit"], 0)
        self.assertEqual(body["general_elective_credit"], 3)
        for lecture in body["lectures"]:
            self.assertIn(lecture["lecture_id"], self.lectures_id)
        self.assertEqual(len(body["lectures"]), 5)

        # 2) lecture already exists in plan.
        data = {
            "semester_id": self.semester_2.id,
            "lecture_id": self.lectures_id
        }
        response = self.client.post(
            '/lecture/', 
            data=data, 
            HTTP_AUTHORIZATION=self.user_token, 
            content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        body = response.json()
        self.assertEqual(body['detail'], "some lecture already exists in plan.")
        
    def test_lecture_list(self):
        """
        Test cases in listing lecture.
            1) search past lectures [major_requirement].
            2) search future lectures [major_requirement].
            3) search past lectures [major_elective].
            4) search future lectures [major_elective].
            5) search past lectures [keyword].
            6) search future lectures [keyword].
        """

        # 1) search past lectures [major_requirement].
        body = {
            "search_type": "major_requirement", 
            "search_year": 2018, 
            "search_keyword":"", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }

        response = self.client.get(
            "/lecture/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        cnt = len(data)
        for i in range(cnt):
            self.assertEqual(data[i]["open_major"], self.major.major_name)
            self.assertEqual(data[i]["lecture_type"], "major_requirement")
            self.assertEqual((data[i]["recent_open_year"]>=2018), True)
            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.existing_lectures_name)
            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)

        # 2) search future lectures [major_requirement].
        body = {
            "search_type": "major_requirement", 
            "search_year": 2021, 
            "search_keyword":"", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        cnt = len(data)
        for i in range(cnt):
            self.assertEqual(data[i]["open_major"], self.major.major_name)
            self.assertEqual(data[i]["lecture_type"], "major_requirement")
            self.assertEqual((data[i]["recent_open_year"]>=2019), True)
            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.existing_lectures_name)
            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)

        # 3) search past lectures [major_elective].
        body = {
            "search_type": "major_elective", 
            "search_year": 2018, 
            "search_keyword":"", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        cnt = len(data)
        for i in range(cnt):
            self.assertEqual(data[i]["open_major"], self.major.major_name)
            self.assertEqual(data[i]["lecture_type"], "major_elective")
            self.assertEqual((data[i]["recent_open_year"]>=2018), True)
            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.existing_lectures_name)
            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)
                
        # 4) search future lectures [major_elective].
        body = {
            "search_type": "major_elective", 
            "search_year": 2021, 
            "search_keyword":"", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        cnt = len(data)
        for i in range(cnt):
            self.assertEqual(data[i]["open_major"], self.major.major_name)
            self.assertEqual(data[i]["lecture_type"], "major_elective")
            self.assertEqual((data[i]["recent_open_year"]>=2019), True)
            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.existing_lectures_name)
            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)

        # 5) search past lectures [keyword].
        body = {
            "search_type": "keyword", 
            "search_year": 2018, 
            "search_keyword":"경영", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        cnt = len(data)
        for i in range(cnt):
            self.assertIn("경영", data[i]["lecture_name"])
            self.assertEqual((data[i]["recent_open_year"]>=2018), True)
            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.existing_lectures_name)

        # 5) search future lectures [keyword].
        body = {
            "search_type": "keyword", 
            "search_year": 2021, 
            "search_keyword":"경영", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        cnt = len(data)
        for i in range(cnt):
            self.assertIn("경영", data[i]["lecture_name"])
            self.assertEqual((data[i]["recent_open_year"]>=2019), True)
            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.existing_lectures_name)


    def test_list_lecture_errors(self):
        """
        Error cases in listing semester lecture.
            1) query parameter missing [search_type].
            2) query parameter missing [search_year].
            3) query parameter missing [plan_id].
            4) query parameter missing [major_name].
            5) plan does not exist.
        """
        # 1) query parameter missing [search_type].
        data = {
            "search_year": 2021, 
            "search_keyword":"경영", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], "query parameter missing [search_type, search_year, plan_id]")

        # 2) query parameter missing [search_year].
        data = {
            "search_type": "keyword", 
            "search_keyword":"경영", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], "query parameter missing [search_type, search_year, plan_id]")

        # 3) query parameter missing [plan_id].
        data = {
            "search_type": "keyword", 
            "search_year": 2021, 
            "search_keyword":"경영", 
            "major_name":self.major.major_name,
        }
        response = self.client.get(
            "/lecture/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], "query parameter missing [search_type, search_year, plan_id]")

        # 4) query parameter missing [major_name].
        data = {
            "search_type": "major_requirement", 
            "search_year": 2021, 
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], "query parameter missing [major_name]")

        # 5) plan does not exist.
        data = {
            "search_type": "major_requirement", 
            "search_year": 2021, 
            "plan_id":9999
        }
        response = self.client.get(
            "/lecture/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        
    def test_lecture_delete(self):
        """
        Test cases in deleting semester lecture.
            1) not semester's owner.
            2) delete semester lecture.
            3) semester lecture not found.
        """
        # 1) not semester's owner
        target = self.semester_2.semesterlecture.filter(lecture__lecture_name="마케팅관리")
        self.assertEqual(target.exists(), True)
        lecture_id = target[0].id

        response = self.client.delete(
            f"/lecture/{lecture_id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2) delete semester lecture.
        response = self.client.delete(
            f"/lecture/{lecture_id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(target.exists(), False)
        self.semester_2.refresh_from_db()
        self.assertEqual(self.semester_2.major_requirement_credit, 3)
        
        # 3) semester lecture not found.
        response = self.client.delete(
            f"/lecture/{lecture_id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LecturePositionTestCase(TestCase):
    """
    # Test Lecture APIs.
        [PUT] lecture/<semesterlecture_id>/position/
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(
            email = "jaejae2374@test.com",
            password = "waffle1234",
            entrance_year = 2018,
            full_name = "test user",
            majors = [{
                "major_name":"경영학과",
                "major_type":"major"
            }],
            status = ACTIVE
        )
        cls.user_token = "Token " + str(cls.user.auth_token)
        cls.stranger = UserFactory.auto_create()
        cls.stranger_token = "Token " + str(cls.stranger.auth_token)
        
        cls.plan = Plan.objects.create(user=cls.user, plan_name="plan example")

        cls.semester_1 = Semester.objects.create(plan=cls.plan, year=2018, semester_type=FIRST)
        cls.semester_2 = Semester.objects.create(
            plan=cls.plan,
            year=2018, 
            semester_type=SECOND,
            major_requirement_credit=6,
            major_elective_credit=3,
            general_credit=3,
            general_elective_credit=3)
        
        cls.major = Major.objects.get(major_name="경영학과", major_type="single_major")
        cls.planmajor = PlanMajor.objects.create(major=cls.major, plan=cls.plan)
        cls.major_lectures_names = [
            "경영과학",
            "마케팅관리",
            "국제경영"
        ]
        cls.general_lectures_names = [
            "법과 문학",
            "알고리즘"
        ]
        cls.major_lectures = Lecture.objects.filter(lecture_name__in=cls.major_lectures_names)
        for idx, lecture in enumerate(list(cls.major_lectures)):
            SemesterLecture.objects.create(
                semester=cls.semester_2,
                lecture=lecture,
                lecture_type=lecture.lecture_type,
                recognized_major1=cls.major,
                lecture_type1=lecture.lecture_type,
                credit=lecture.credit,
                recent_sequence=idx
                )
        cls.lecture_general = Lecture.objects.get(lecture_name="법과 문학")
        SemesterLecture.objects.create(
            semester=cls.semester_2,
            lecture=cls.lecture_general,
            lecture_type=cls.lecture_general.lecture_type,
            lecture_type1=cls.lecture_general.lecture_type,
            credit=cls.lecture_general.credit,
            recent_sequence=idx+1
            )
        cls.lecture_general_elective = Lecture.objects.get(lecture_name="알고리즘")
        SemesterLecture.objects.create(
            semester=cls.semester_2,
            lecture=cls.lecture_general_elective,
            lecture_type=GENERAL_ELECTIVE,
            lecture_type1=GENERAL_ELECTIVE,
            credit=cls.lecture_general_elective.credit,
            recent_sequence=idx+2
            )
    
    
    def test_lecture_position(self):
        """
        Test cases in positioning semester lecture.
            1) position major_requirement lecture [position=0].
            2) position major_elective lecture [position=1].
            3) position general lecture [position=1].
            4) position general_elective lecture [position=2].
            5) semester lecture does not exist.
            6) Field missing [semester_to].
            7) semester does not exist.
            8) Invalid field [position].
            9) not semesterlecture's owner.
        """
        histories = []

        # 1) position major_requirement lecture [position=0].
        target_lecture = self.semester_2.semesterlecture.filter(lecture_type=MAJOR_REQUIREMENT)[0]
        lecture_instance = target_lecture.lecture
        target_lecture_name = lecture_instance.lecture_name
        before_credit_from = self.semester_2.major_requirement_credit
        before_credit_to = self.semester_1.major_requirement_credit
        histories.insert(0, lecture_instance)

        data = {
            "semester_to": self.semester_1.id,
            "position": 0
        }

        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.semester_1.refresh_from_db()
        self.semester_2.refresh_from_db()
        semester_from = data[0]
        semester_to = data[1]

        self.assertEqual(semester_from['year'], 2018)
        self.assertEqual(semester_from['semester_type'], SECOND)
        self.assertEqual(semester_from['major_requirement_credit'], before_credit_from-3)
        self.assertEqual(semester_from['major_elective_credit'], self.semester_2.major_elective_credit)
        self.assertEqual(semester_from['general_credit'], self.semester_2.general_credit)
        self.assertEqual(semester_from['general_elective_credit'], self.semester_2.general_elective_credit)
        self.assertEqual(len(semester_from['lectures']), 4)
        for i, lecture in enumerate(semester_from['lectures']) :
            self.assertNotEqual(lecture["lecture_name"], target_lecture_name)
            self.assertEqual(lecture['recent_sequence'], i)
        self.assertEqual(
            self.semester_2.semesterlecture.filter(
                lecture=lecture_instance).exists(), False)

        self.assertEqual(semester_to['year'], 2018)
        self.assertEqual(semester_to['semester_type'], FIRST)
        self.assertEqual(semester_to['major_requirement_credit'], before_credit_to+3)
        self.assertEqual(semester_to['major_elective_credit'], self.semester_1.major_elective_credit)
        self.assertEqual(semester_to['general_credit'], self.semester_1.general_credit)
        self.assertEqual(semester_to['general_elective_credit'], self.semester_1.general_elective_credit)
        
        self.assertEqual(semester_to['lectures'][0]["lecture_name"], target_lecture_name)
        self.assertEqual(semester_to['lectures'][0]['recent_sequence'], 0)
        self.assertEqual(
            self.semester_1.semesterlecture.filter(
                lecture=lecture_instance).exists(), True)

        # 2) position major_elective lecture [position=1].
        target_lecture = self.semester_2.semesterlecture.filter(lecture_type=MAJOR_ELECTIVE)[0]
        lecture_instance = target_lecture.lecture
        target_lecture_name = lecture_instance.lecture_name
        before_credit_from = self.semester_2.major_elective_credit
        before_credit_to = self.semester_1.major_elective_credit
        histories.insert(1, lecture_instance)

        data = {
            "semester_to": self.semester_1.id,
            "position": 1
        }

        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.semester_1.refresh_from_db()
        self.semester_2.refresh_from_db()
        semester_from = data[0]
        semester_to = data[1]

        self.assertEqual(semester_from['year'], 2018)
        self.assertEqual(semester_from['semester_type'], SECOND)
        self.assertEqual(semester_from['major_requirement_credit'], self.semester_2.major_requirement_credit)
        self.assertEqual(semester_from['major_elective_credit'], before_credit_from-3)
        self.assertEqual(semester_from['general_credit'], self.semester_2.general_credit)
        self.assertEqual(semester_from['general_elective_credit'], self.semester_2.general_elective_credit)
        self.assertEqual(len(semester_from['lectures']), 3)
        for i, lecture in enumerate(semester_from['lectures']) :
            self.assertNotEqual(lecture["lecture_name"], target_lecture_name)
            self.assertEqual(lecture['recent_sequence'], i)
        self.assertEqual(
            self.semester_2.semesterlecture.filter(
                lecture=lecture_instance).exists(), False)

        self.assertEqual(semester_to['year'], 2018)
        self.assertEqual(semester_to['semester_type'], FIRST)
        self.assertEqual(semester_to['major_requirement_credit'], self.semester_1.major_requirement_credit)
        self.assertEqual(semester_to['major_elective_credit'], before_credit_to+3)
        self.assertEqual(semester_to['general_credit'], self.semester_1.general_credit)
        self.assertEqual(semester_to['general_elective_credit'], self.semester_1.general_elective_credit)
        
        self.assertEqual(semester_to['lectures'][1]["lecture_name"], target_lecture_name)
        self.assertEqual(semester_to['lectures'][1]['recent_sequence'], 1)
        self.assertEqual(
            self.semester_1.semesterlecture.filter(
                lecture=lecture_instance).exists(), True)

        # 3) position general lecture [position=1].
        target_lecture = self.semester_2.semesterlecture.filter(lecture_type=GENERAL)[0]
        lecture_instance = target_lecture.lecture
        target_lecture_name = lecture_instance.lecture_name
        before_credit_from = self.semester_2.general_credit
        before_credit_to = self.semester_1.general_credit
        histories.insert(1, lecture_instance)

        data = {
            "semester_to": self.semester_1.id,
            "position": 1
        }

        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.semester_1.refresh_from_db()
        self.semester_2.refresh_from_db()
        semester_from = data[0]
        semester_to = data[1]

        self.assertEqual(semester_from['year'], 2018)
        self.assertEqual(semester_from['semester_type'], SECOND)
        self.assertEqual(semester_from['major_requirement_credit'], self.semester_2.major_requirement_credit)
        self.assertEqual(semester_from['major_elective_credit'], self.semester_2.major_elective_credit)
        self.assertEqual(semester_from['general_credit'], before_credit_from-3)
        self.assertEqual(semester_from['general_elective_credit'], self.semester_2.general_elective_credit)
        self.assertEqual(len(semester_from['lectures']), 2)
        for i, lecture in enumerate(semester_from['lectures']) :
            self.assertNotEqual(lecture["lecture_name"], target_lecture_name)
            self.assertEqual(lecture['recent_sequence'], i)
        self.assertEqual(
            self.semester_2.semesterlecture.filter(
                lecture=lecture_instance).exists(), False)

        self.assertEqual(semester_to['year'], 2018)
        self.assertEqual(semester_to['semester_type'], FIRST)
        self.assertEqual(semester_to['major_requirement_credit'], self.semester_1.major_requirement_credit)
        self.assertEqual(semester_to['major_elective_credit'], self.semester_1.major_elective_credit)
        self.assertEqual(semester_to['general_credit'], before_credit_to+3)
        self.assertEqual(semester_to['general_elective_credit'], self.semester_1.general_elective_credit)
        
        self.assertEqual(semester_to['lectures'][1]["lecture_name"], target_lecture_name)
        self.assertEqual(semester_to['lectures'][1]['recent_sequence'], 1)
        self.assertEqual(
            self.semester_1.semesterlecture.filter(
                lecture=lecture_instance).exists(), True)

        # 4) position general_elective lecture [position=2].
        target_lecture = self.semester_2.semesterlecture.filter(lecture_type=GENERAL_ELECTIVE)[0]
        lecture_instance = target_lecture.lecture
        target_lecture_name = lecture_instance.lecture_name
        before_credit_from = self.semester_2.general_elective_credit
        before_credit_to = self.semester_1.general_elective_credit
        histories.insert(2, lecture_instance)

        data = {
            "semester_to": self.semester_1.id,
            "position": 2
        }

        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.semester_1.refresh_from_db()
        self.semester_2.refresh_from_db()
        semester_from = data[0]
        semester_to = data[1]

        self.assertEqual(semester_from['year'], 2018)
        self.assertEqual(semester_from['semester_type'], SECOND)
        self.assertEqual(semester_from['major_requirement_credit'], self.semester_2.major_requirement_credit)
        self.assertEqual(semester_from['major_elective_credit'], self.semester_2.major_elective_credit)
        self.assertEqual(semester_from['general_credit'], self.semester_2.general_credit)
        self.assertEqual(semester_from['general_elective_credit'], before_credit_from-3)
        self.assertEqual(len(semester_from['lectures']), 1)
        for i, lecture in enumerate(semester_from['lectures']) :
            self.assertNotEqual(lecture["lecture_name"], target_lecture_name)
            self.assertEqual(lecture['recent_sequence'], i)
        self.assertEqual(
            self.semester_2.semesterlecture.filter(
                lecture=lecture_instance).exists(), False)

        self.assertEqual(semester_to['year'], 2018)
        self.assertEqual(semester_to['semester_type'], FIRST)
        self.assertEqual(semester_to['major_requirement_credit'], self.semester_1.major_requirement_credit)
        self.assertEqual(semester_to['major_elective_credit'], self.semester_1.major_elective_credit)
        self.assertEqual(semester_to['general_credit'], self.semester_1.general_credit)
        self.assertEqual(semester_to['general_elective_credit'], before_credit_to+3)
        
        for i, lec in enumerate(histories):
            self.assertEqual(semester_to['lectures'][i]["lecture_name"], lec.lecture_name)
            self.assertEqual(semester_to['lectures'][i]['recent_sequence'], i)
        self.assertEqual(
            self.semester_1.semesterlecture.filter(
                lecture=lecture_instance).exists(), True)

        # 5) semester lecture does not exist.
        data = {
            "semester_to": self.semester_1.id,
            "position": 2
        }
        response = self.client.put(
            "/lecture/9999/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 6) Field missing [semester_to]
        target_lecture = self.semester_2.semesterlecture.filter(lecture_type=MAJOR_REQUIREMENT)[0]
        data = {
            "position": 2
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["detail"], "Field missing [semester_to]")

        # 7) semester does not exist
        data = {
            "semester_to": 9999
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertEqual(data["detail"], "semester does not exist")

        # 8) Invalid field [position]
        data = {
            "semester_to": self.semester_1.id,
            "position": 5
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["detail"], "Invalid field [position]")

        data = {
            "semester_to": self.semester_1.id,
            "position": -1
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["detail"], "Invalid field [position]")

        # 9) not semesterlecture's owner.
        data = {
            "semester_to": self.semester_1.id,
            "position": 2
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LectureChangeTestCase(TestCase):
    """
    # Test Lecture APIs.
        [PUT] lecture/<semesterLecture_id>/credit/
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(
            email = "jaejae2374@test.com",
            password = "waffle1234",
            entrance_year = 2018,
            full_name = "test user",
            majors = [{
                "major_name":"경영학과",
                "major_type":"major"
            }],
            status = ACTIVE
        )
        cls.user_token = "Token " + str(cls.user.auth_token)
        cls.stranger = UserFactory.auto_create()
        cls.stranger_token = "Token " + str(cls.stranger.auth_token)
        
        cls.plan = Plan.objects.create(user=cls.user, plan_name="plan example")

        cls.semester = Semester.objects.create(
            plan=cls.plan,
            year=2018, 
            semester_type=SECOND,
            major_requirement_credit=3,
            major_elective_credit=3,
            general_credit=3,
            general_elective_credit=3)
        
        cls.major_1 = Major.objects.get(major_name="경영학과", major_type="major")
        cls.planmajor_1 = PlanMajor.objects.create(major=cls.major_1, plan=cls.plan)
        cls.major_2 = Major.objects.get(major_name="심리학과", major_type="double_major")
        cls.planmajor_2 = PlanMajor.objects.create(major=cls.major_2, plan=cls.plan)
        cls.major_lectures_names = [
            "마케팅관리",
            "국제경영"
        ]
        cls.major_lectures = Lecture.objects.filter(lecture_name__in=cls.major_lectures_names)
        for idx, lecture in enumerate(list(cls.major_lectures)):
            SemesterLecture.objects.create(
                semester=cls.semester,
                lecture=lecture,
                lecture_type=lecture.lecture_type,
                recognized_major1=cls.major_1,
                lecture_type1=lecture.lecture_type,
                credit=lecture.credit,
                recent_sequence=idx
                )
        cls.lecture_general = Lecture.objects.get(lecture_name="법과 문학")
        SemesterLecture.objects.create(
            semester=cls.semester,
            lecture=cls.lecture_general,
            lecture_type=cls.lecture_general.lecture_type,
            lecture_type1=cls.lecture_general.lecture_type,
            credit=cls.lecture_general.credit,
            recent_sequence=idx+1
            )
        cls.lecture_general_elective = Lecture.objects.get(lecture_name="알고리즘")
        SemesterLecture.objects.create(
            semester=cls.semester,
            lecture=cls.lecture_general_elective,
            lecture_type=GENERAL_ELECTIVE,
            lecture_type1=GENERAL_ELECTIVE,
            credit=cls.lecture_general_elective.credit,
            recent_sequence=idx+2
            )

        cls.none_major = Major.objects.get(id=DEFAULT_MAJOR_ID)


    def test_change_credit(self):
        """
        Test cases in changing semester lecture credit.
            1) change major_requirement semester lecture credit.
            2) change major_elective semester lecture credit.
            3) change general semester lecture credit.
            4) change general_elective semester lecture credit.
            5) change major_requirement semester lecture credit again.
            6) Invalid field [credit].
            7) semesterlecture does not exist.
            8) not semesterlecture's owner
        """
        # 1) change major_requirement semester lecture credit.
        target_lecture = self.semester.semesterlecture.get(lecture_type=MAJOR_REQUIREMENT)
        before_semester_credit = self.semester.major_requirement_credit
        data = {
            "credit": 4
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['credit'], 4)
        self.assertEqual(data['is_modified'], True)
        self.semester.refresh_from_db()
        self.assertEqual(self.semester.major_requirement_credit, before_semester_credit+1)
        self.assertEqual(
            CreditChangeHistory.objects.filter(
                lecture=target_lecture.lecture,
                entrance_year=2018,
                year_taken=self.semester.year,
                past_credit=3,
                curr_credit=4,
                change_count=1
            ).exists(), True
        )

        # 2) change major_elective semester lecture credit.
        target_lecture = self.semester.semesterlecture.get(lecture_type=MAJOR_ELECTIVE)
        before_semester_credit = self.semester.major_elective_credit
        data = {
            "credit": 2
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['credit'], 2)
        self.assertEqual(data['is_modified'], True)
        self.semester.refresh_from_db()
        self.assertEqual(self.semester.major_elective_credit, before_semester_credit-1)
        self.assertEqual(
            CreditChangeHistory.objects.filter(
                lecture=target_lecture.lecture,
                entrance_year=2018,
                year_taken=self.semester.year,
                past_credit=3,
                curr_credit=2,
                change_count=1
            ).exists(), True
        )

        # 3) change general semester lecture credit.
        target_lecture = self.semester.semesterlecture.get(lecture_type=GENERAL)
        before_semester_credit = self.semester.general_credit
        data = {
            "credit": 1
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['credit'], 1)
        self.assertEqual(data['is_modified'], True)
        self.semester.refresh_from_db()
        self.assertEqual(self.semester.general_credit, before_semester_credit-2)
        self.assertEqual(
            CreditChangeHistory.objects.filter(
                lecture=target_lecture.lecture,
                entrance_year=2018,
                year_taken=self.semester.year,
                past_credit=3,
                curr_credit=1,
                change_count=1
            ).exists(), True
        )

        # 4) change general_elective semester lecture credit.
        target_lecture = self.semester.semesterlecture.get(lecture_type=GENERAL_ELECTIVE)
        before_semester_credit = self.semester.general_elective_credit
        data = {
            "credit": 4
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['credit'], 4)
        self.assertEqual(data['is_modified'], True)
        self.semester.refresh_from_db()
        self.assertEqual(self.semester.general_elective_credit, before_semester_credit+1)
        self.assertEqual(
            CreditChangeHistory.objects.filter(
                lecture=target_lecture.lecture,
                entrance_year=2018,
                year_taken=self.semester.year,
                past_credit=3,
                curr_credit=4,
                change_count=1
            ).exists(), True
        )

        # 5) change major_requirement semester lecture credit again.
        target_lecture = self.semester.semesterlecture.get(lecture_type=MAJOR_REQUIREMENT)
        data = {
            "credit": 3
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            "credit": 4
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(
            CreditChangeHistory.objects.filter(
                lecture=target_lecture.lecture,
                entrance_year=2018,
                year_taken=self.semester.year,
                past_credit=3,
                curr_credit=4,
                change_count=2
            ).exists(), True
        )

        # 6) Invalid field [credit].
        target_lecture = self.semester.semesterlecture.get(lecture_type=MAJOR_REQUIREMENT)
        data = {
            "credit": 5
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], "Invalid field [credit]")

        data = {
            "credit": 0
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], "Invalid field [credit]")

        # 7) semesterlecture does not exist.
        data = {
            "credit": 3
        }
        response = self.client.put(
            "/lecture/9999/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()

        # 8) not semesterlecture's owner
        data = {
            "credit": 3
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/credit/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    
    def test_change_recognized_major(self):
        """
        Test cases in changing semester lecture major, major_type, lecture_type.
            1) change major_requirement semester lecture to major_elective.
            2) change major_elective semester lecture to general.
            3) change general semester lecture to general_elective.
            4) change general_elective semester to major_requirement.
            5) semesterlecture does not exist.
            6) not semesterlecture's owner.
            7) major does not exist.
            8) Invalid field [lecture_type].
        """
        # 1) change major_requirement semester lecture to major_elective.
        target_lecture = self.semester.semesterlecture.get(lecture_type=MAJOR_REQUIREMENT)
        before_major_requirement_credit = self.semester.major_requirement_credit
        before_major_elective_credit = self.semester.major_elective_credit
        body = {
            "lecture_type": MAJOR_ELECTIVE,
            "recognized_major_name1":"경영학과",
            "recognized_major_type1":"major",
            "recognized_major_name2":"심리학과",
            "recognized_major_type2":"double_major",
            "lecture_type1":MAJOR_ELECTIVE,
            "lecture_type2":MAJOR_ELECTIVE,
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["lecture_type"], MAJOR_ELECTIVE)
        self.assertEqual(data["lecture_type1"], MAJOR_ELECTIVE)
        self.assertEqual(data["lecture_type2"], MAJOR_ELECTIVE)
        self.assertEqual(data["recognized_major1"], self.major_1.id)
        self.assertEqual(data["recognized_major2"], self.major_2.id)
        self.semester.refresh_from_db()
        self.assertEqual(before_major_requirement_credit-3, self.semester.major_requirement_credit)
        self.assertEqual(before_major_elective_credit+3, self.semester.major_elective_credit)
        self.assertEqual(
            LectureTypeChangeHistory.objects.filter(
                major=self.major_1,
                lecture=target_lecture.lecture,
                entrance_year=2018,
                past_lecture_type=MAJOR_REQUIREMENT,
                curr_lecture_type=MAJOR_ELECTIVE,
                change_count=1
            ).exists(), True
        )
        self.assertEqual(
            LectureTypeChangeHistory.objects.filter(
                major=self.major_2,
                lecture=target_lecture.lecture,
                entrance_year=2018,
                past_lecture_type=NONE,
                curr_lecture_type=MAJOR_ELECTIVE,
                change_count=1
            ).exists(), True
        )

        # 2) change major_elective semester lecture to general.
        target_lecture = self.semester.semesterlecture.get(lecture_type=MAJOR_ELECTIVE, lecture_type2=NONE)
        before_major_elective_credit = self.semester.major_elective_credit
        before_general_credit = self.semester.general_credit
        body = {
            "lecture_type": GENERAL
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["lecture_type"], GENERAL)
        self.assertEqual(data["lecture_type1"], GENERAL)
        self.assertEqual(data["lecture_type2"], NONE)
        self.assertEqual(data["recognized_major1"], DEFAULT_MAJOR_ID)
        self.assertEqual(data["recognized_major2"], DEFAULT_MAJOR_ID)
        self.semester.refresh_from_db()
        self.assertEqual(before_major_elective_credit-3, self.semester.major_elective_credit)
        self.assertEqual(before_general_credit+3, self.semester.general_credit)
        self.assertEqual(
            LectureTypeChangeHistory.objects.filter(
                major=self.none_major,
                lecture=target_lecture.lecture,
                entrance_year=2018,
                past_lecture_type=NONE,
                curr_lecture_type=GENERAL,
                change_count=1
            ).exists(), True
        )
        self.assertEqual(
            LectureTypeChangeHistory.objects.filter(
                major=self.major_1,
                lecture=target_lecture.lecture,
                entrance_year=2018,
                past_lecture_type=MAJOR_ELECTIVE,
                curr_lecture_type=NONE,
                change_count=1
            ).exists(), True
        )

        # 3) change general semester lecture to general_elective.
        target_lecture = self.semester.semesterlecture.get(lecture__lecture_name="법과 문학")
        before_general_credit = self.semester.general_credit
        before_general_elective_credit = self.semester.general_elective_credit
        body = {
            "lecture_type": GENERAL_ELECTIVE
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["lecture_type"], GENERAL_ELECTIVE)
        self.assertEqual(data["lecture_type1"], GENERAL_ELECTIVE)
        self.assertEqual(data["lecture_type2"], NONE)
        self.assertEqual(data["recognized_major1"], DEFAULT_MAJOR_ID)
        self.assertEqual(data["recognized_major2"], DEFAULT_MAJOR_ID)
        self.semester.refresh_from_db()
        self.assertEqual(before_general_credit-3, self.semester.general_credit)
        self.assertEqual(before_general_elective_credit+3, self.semester.general_elective_credit)
        self.assertEqual(
            LectureTypeChangeHistory.objects.filter(
                major=self.none_major,
                lecture=target_lecture.lecture,
                entrance_year=2018,
                past_lecture_type=NONE,
                curr_lecture_type=GENERAL_ELECTIVE,
                change_count=1
            ).exists(), True
        )

        # 4) change general_elective semester to major_requirement.
        target_lecture = self.semester.semesterlecture.get(lecture__lecture_name="알고리즘")
        before_major_requirement_credit = self.semester.major_requirement_credit
        before_general_elective_credit = self.semester.general_elective_credit
        body = {
            "lecture_type": MAJOR_REQUIREMENT,
            "recognized_major_name1":"경영학과",
            "recognized_major_type1":"major",
            "lecture_type1": MAJOR_REQUIREMENT,
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["lecture_type"], MAJOR_REQUIREMENT)
        self.assertEqual(data["lecture_type1"], MAJOR_REQUIREMENT)
        self.assertEqual(data["recognized_major1"], self.major_1.id)
        self.semester.refresh_from_db()
        self.assertEqual(before_general_elective_credit-3, self.semester.general_elective_credit)
        self.assertEqual(before_major_requirement_credit+3, self.semester.major_requirement_credit)
        l = LectureTypeChangeHistory.objects.get(lecture=target_lecture.lecture)
        self.assertEqual(
            LectureTypeChangeHistory.objects.filter(
                major=self.major_1,
                lecture=target_lecture.lecture,
                entrance_year=2018,
                past_lecture_type=NONE,
                curr_lecture_type=MAJOR_REQUIREMENT,
                change_count=1
            ).exists(), True
        )

        # 5) semesterlecture does not exist.
        response = self.client.put(
            "/lecture/9999/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 6) not semesterlecture's owner.
        response = self.client.put(
             f"/lecture/{target_lecture.id}/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.stranger_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 7) major does not exist.
        body = {
            "lecture_type": MAJOR_REQUIREMENT,
            "recognized_major_name1":"와플학과",
            "recognized_major_type1":"major",
            "lecture_type1": MAJOR_REQUIREMENT,
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 8) Invalid field [lecture_type]
        body = {
            "lecture_type": "wrong_type",
            "recognized_major_name1":"경영학과",
            "recognized_major_type1":"major",
            "lecture_type1": MAJOR_REQUIREMENT,
        }
        response = self.client.put(
            f"/lecture/{target_lecture.id}/recognized_major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], "Invalid field [lecture_type]")
