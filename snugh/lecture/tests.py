from django.test import TestCase
from rest_framework import status
from user.utils import UserFactory

from user.models import Major
from lecture.models import Lecture, SemesterLecture
from plan.models import Plan, PlanMajor
from semester.models import Semester
from user.const import *
from semester.const import *

class LectureTestCase(TestCase):
    """
    # Test Lecture APIs.
        [POST] lecture/
        [GET] lecture/
        [DELETE] lecture/
        [PUT] lecture/<lecture_id>/position/
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
            sl = SemesterLecture.objects.create(
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


    # # PUT lecture/<lecture_id>/position
    # def test_lecture_position(self):
    #     """
    #     Test [PUT] lecture/<lecture_id>/position
    #     """

    #     lectures_2016 = self.lectures
    #     target_lecture = lectures_2016.get(lecture_name="경영과학")

    #     semester_from_id = self.semester_2016.id
    #     semester_to_id = self.semester_2021.id

    #     semester_to_list = [target_lecture.id]
    #     semester_from_list = list(lectures_2016.exclude(lecture_name="경영과학").values_list("id", flat=True))
        
    #     body = {
    #         "semester_to_id":semester_to_id,
    #         "semester_from_id":semester_from_id,
    #         "semester_to":semester_to_list,
    #         "semester_from":semester_from_list
    #     }

    #     response = self.client.put(
    #         f"/lecture/{target_lecture.id}/position/",
    #         data=body,
    #         content_type="application/json",
    #         HTTP_AUTHORIZATION=self.user_token,
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = response.json()

    #     self.assertEqual(data[0]['year'], 2016)
    #     self.assertEqual(data[0]['semester_type'], "first")
    #     self.assertEqual(data[0]['major_requirement_credit'], self.semester_2016.major_requirement_credit-3)
    #     self.assertEqual(data[0]['major_elective_credit'], self.semester_2016.major_elective_credit)
        
    #     for i, lecture in enumerate(data[0]['lectures']) :
    #         self.assertNotEqual(lecture["lecture_name"], "경영과학")
    #         self.assertEqual(lecture['recent_sequence'], i)
    #     self.assertEqual(
    #         self.semester_2016.semesterlecture.filter(
    #             lecture=target_lecture).exists(), False)

    #     self.assertEqual(data[1]['year'], 2021)
    #     self.assertEqual(data[1]['semester_type'], "first")
    #     self.assertEqual(data[1]['major_requirement_credit'], self.semester_2021.major_requirement_credit+3)
    #     self.assertEqual(data[1]['major_elective_credit'], self.semester_2021.major_elective_credit)
        
    #     self.assertEqual(data[1]['lectures'][0]["lecture_name"], '경영과학')
    #     self.assertEqual(data[1]['lectures'][0]['recent_sequence'], 0)
    #     self.assertEqual(
    #         self.semester_2021.semesterlecture.filter(
    #             lecture=target_lecture).exists(), True)

    #     # 원래는 에러가 발생해야하는 상황
    #     # 디자인 사고와 혁신 과목이 2016년에 마지막으로 열린 강의라서
    #     # 2021년도 학기에 추가가 되지 말아야 함
    #     target_lecture = lectures_2016.get(lecture_name="디자인 사고와 혁신")
    #     semester_to_list.insert(0, target_lecture.id)
    #     semester_from_list = list(lectures_2016.exclude(
    #         lecture_name__in=["경영과학", "디자인 사고와 혁신"]).values_list("id", flat=True))

    #     body = {
    #         "semester_to_id":semester_to_id,
    #         "semester_from_id":semester_from_id,
    #         "semester_to":semester_to_list,
    #         "semester_from":semester_from_list
    #     }

    #     response = self.client.put(
    #         f"/lecture/{target_lecture.id}/position/",
    #         data=body,
    #         content_type="application/json",
    #         HTTP_AUTHORIZATION=self.user_token,
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = response.json()


