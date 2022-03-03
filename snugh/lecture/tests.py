from django.test import TestCase
from user.models import User, Major, UserMajor, UserProfile
from rest_framework import status
from pathlib import Path
from django.db.models import Q
from user.utils import UserFactory, UserMajorFactory
from .utils import SemesterFactory, SemesterLectureFactory
from .models import Lecture, Plan, PlanMajor, Semester, SemesterLecture

BASE_DIR = Path(__file__).resolve().parent.parent


class LectureListDeleteTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory.create()
        cls.user_token = "Token " + str(cls.user.auth_token)
        
        cls.plan = Plan.objects.create(user=cls.user, plan_name="test")

        cls.semesters = SemesterFactory.create(
            semesters=[
                {
                    "plan":cls.plan,
                    "year":2016,
                    "semester_type":"first",
                    "major_requirement_credit":6,
                    "major_elective_credit":9
                },
                {
                    "plan":cls.plan,
                    "year":2021,
                    "semester_type":"first"
                }
            ]
        )
        
        # bulk_create()가 mysql에서는 id가 none인 저장 안된 object들을 retrieve하기 때문에
        # .get으로 별도로 retrieve 해줬습니다. 
        cls.semester_2016 = Semester.objects.get(year=2016, semester_type="first")
        cls.semester_2021 = Semester.objects.get(year=2021, semester_type="first")
        cls.major = Major.objects.get(major_name="경영학과", major_type="major")
        cls.planmajor = PlanMajor.objects.create(major=cls.major, plan=cls.plan)
        cls.my_lectures = [
            "경영과학", 
            "디자인 사고와 혁신", 
            "고급회계",
            "공급사슬관리",
            "국제경영"
        ]
        cls.lectures = Lecture.objects.filter(lecture_name__in=cls.my_lectures)

        cls.semesterlectures = SemesterLectureFactory.create(
            semester=cls.semester_2016,
            lectures=cls.lectures,
            recognized_majors=[cls.major]*5
        )
        
    # GET /lecture/
    def test_lecture_list(self):

        # 과거 기준 전필 조회
        body = {
            "search_type": "major_requirement", 
            "search_year": 2016, 
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
            self.assertEqual((data[i]["recent_open_year"]>=2016), True)

            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.my_lectures)

            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)

        # 미래 기준 전필 조회
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
            self.assertNotIn(data[i]["lecture_name"], self.my_lectures)

            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)

        # 과거 기준 전선 조회
        body = {
            "search_type": "major_elective", 
            "search_year": 2016, 
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
            self.assertEqual((data[i]["recent_open_year"]>=2016), True)

            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.my_lectures)

            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)
                
        # 미래 기준 전선 조회
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
            self.assertNotIn(data[i]["lecture_name"], self.my_lectures)

            if i!=cnt-1:
                # 정렬 check
                self.assertEqual((data[i]["lecture_name"]<=data[i+1]["lecture_name"]), True)


        # 과거 기준 키워드 검색
        body = {
            "search_type": "keyword", 
            "search_year": 2016, 
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
            self.assertEqual((data[i]["recent_open_year"]>=2016), True)

            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.my_lectures)

        # 미래 기준 키워드 검색
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
            self.assertEqual((data[i]["recent_open_year"]>=2016), True)

            # 이미 추가한 강의 있는지 check
            self.assertNotIn(data[i]["lecture_name"], self.my_lectures)

    def test_lecture_list_error(self):

        wrong_body = {
            "search_type": "", 
            "search_year": 2021, 
            "search_keyword":"", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=wrong_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error'], "search_type missing")

        wrong_body = {
            "search_type": "major_elective", 
            "search_keyword":"", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=wrong_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error'], "search_year missing")

        wrong_body = {
            "search_type": "keyword", 
            "search_keyword":"", 
            "major_name":self.major.major_name,
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=wrong_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error'], "search_year missing")

        wrong_body = {
            "search_type": "major_requirement", 
            "search_year": 2021, 
            "search_keyword":"", 
            "major_name":"",
            "plan_id":self.plan.id
        }
        response = self.client.get(
            "/lecture/",
            data=wrong_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error'], "major_name missing")

        wrong_body = {
            "search_type": "major_requirement", 
            "search_year": 2021, 
            "search_keyword":"", 
            "major_name":self.major.major_name
        }
        response = self.client.get(
            "/lecture/",
            data=wrong_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error'], "plan_id missing")

        wrong_body = {
            "search_type": "keyword", 
            "search_year": 2021, 
            "search_keyword":"", 
            "major_name":self.major.major_name
        }
        response = self.client.get(
            "/lecture/",
            data=wrong_body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error'], "plan_id missing")
        
        
    # DELETE /lecture/
    def test_lecture_delete(self):
        
        self.assertEqual(
            self.semester_2016.semesterlecture.filter(
                lecture__lecture_name="공급사슬관리").exists(), True)
        lecture_id = self.semester_2016.semesterlecture.get(lecture__lecture_name="공급사슬관리").id
        
        response = self.client.delete(
            f"/lecture/{lecture_id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.semester_2016.semesterlecture.filter(
                lecture__lecture_name="공급사슬관리").exists(), False)

        response = self.client.delete(
            f"/lecture/{lecture_id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.semester_2016.refresh_from_db()
        self.assertEqual(self.semester_2016.major_elective_credit, 6)

    # PUT lecture/<lecture_id>/position
    def test_lecture_position(self):

        lectures_2016 = self.lectures
        target_lecture = lectures_2016.get(lecture_name="경영과학")

        semester_from_id = self.semester_2016.id
        semester_to_id = self.semester_2021.id

        semester_to_list = [target_lecture.id]
        semester_from_list = list(lectures_2016.exclude(lecture_name="경영과학").values_list("id", flat=True))
        
        body = {
            "semester_to_id":semester_to_id,
            "semester_from_id":semester_from_id,
            "semester_to":semester_to_list,
            "semester_from":semester_from_list
        }

        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data[0]['year'], 2016)
        self.assertEqual(data[0]['semester_type'], "first")
        self.assertEqual(data[0]['major_requirement_credit'], self.semester_2016.major_requirement_credit-3)
        self.assertEqual(data[0]['major_elective_credit'], self.semester_2016.major_elective_credit)
        
        for i, lecture in enumerate(data[0]['lectures']) :
            self.assertNotEqual(lecture["lecture_name"], "경영과학")
            self.assertEqual(lecture['recent_sequence'], i)
        self.assertEqual(
            self.semester_2016.semesterlecture.filter(
                lecture=target_lecture).exists(), False)

        self.assertEqual(data[1]['year'], 2021)
        self.assertEqual(data[1]['semester_type'], "first")
        self.assertEqual(data[1]['major_requirement_credit'], self.semester_2021.major_requirement_credit+3)
        self.assertEqual(data[1]['major_elective_credit'], self.semester_2021.major_elective_credit)
        
        self.assertEqual(data[1]['lectures'][0]["lecture_name"], '경영과학')
        self.assertEqual(data[1]['lectures'][0]['recent_sequence'], 0)
        self.assertEqual(
            self.semester_2021.semesterlecture.filter(
                lecture=target_lecture).exists(), True)

        # 원래는 에러가 발생해야하는 상황
        # 디자인 사고와 혁신 과목이 2016년에 마지막으로 열린 강의라서
        # 2021년도 학기에 추가가 되지 말아야 함
        target_lecture = lectures_2016.get(lecture_name="디자인 사고와 혁신")
        semester_to_list.insert(0, target_lecture.id)
        semester_from_list = list(lectures_2016.exclude(
            lecture_name__in=["경영과학", "디자인 사고와 혁신"]).values_list("id", flat=True))

        body = {
            "semester_to_id":semester_to_id,
            "semester_from_id":semester_from_id,
            "semester_to":semester_to_list,
            "semester_from":semester_from_list
        }

        response = self.client.put(
            f"/lecture/{target_lecture.id}/position/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

    