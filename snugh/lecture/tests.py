from sqlite3 import DataError
from django.test import TestCase
from user.models import User, Major, UserMajor, UserProfile
from rest_framework import status
from pathlib import Path
from django.db.models import Q
from user.utils import UserFactory, UserMajorFactory
from .utils import SemesterFactory, SemesterLectureFactory
from .models import Lecture, Plan, PlanMajor, Semester, SemesterLecture

BASE_DIR = Path(__file__).resolve().parent.parent


class LectureTestCase(TestCase):
    """
    # Test

    [GET] lecture/
    [DELETE] lecture/
    [PUT] lecture/<lecture_id>/position/
    """

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
        
    def test_lecture_list(self):
        """
        Test [GET] lecture/
        """

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
        """
        Test error [GET] lecture/ 
        """

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
        
        
    def test_lecture_delete(self):
        """
        Test [DELETE] lecture/
        """
        
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
        """
        Test [PUT] lecture/<lecture_id>/position
        """

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

class SemesterTestCase(TestCase):
    """
    # Test 

    [GET] semester/<semester_id>/
    [DELETE] semester/<semester_id>/
    [PUT] semester/<semester_id>/
    """
    
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
                },
                {
                    "plan":cls.plan,
                    "year":2021,
                    "semester_type":"second"
                }
            ]
        )
        
        # bulk_create()가 mysql에서는 id가 none인 저장 안된 object들을 retrieve하기 때문에
        # .get으로 별도로 retrieve 해줬습니다. 
        cls.semester_2016 = Semester.objects.get(year=2016, semester_type="first")
        
        # for testing deletion
        cls.semester_2021 = Semester.objects.get(year=2021, semester_type="first")
        
        cls.major = Major.objects.get(major_name="경영학과", major_type="major")
        cls.planmajor = PlanMajor.objects.create(major=cls.major, plan=cls.plan)
        cls.lectures_list_2016 = [
            "경영과학", 
            "고급회계",
            "공급사슬관리",
            "국제경영",
            "디자인 사고와 혁신" 
        ]
        cls.lectures_2016 = Lecture.objects.filter(lecture_name__in=cls.lectures_list_2016)

        cls.semesterlectures_2016 = SemesterLectureFactory.create(
            semester=cls.semester_2016,
            lectures=cls.lectures_2016,
            recognized_majors=[cls.major]*5
        )

        cls.semesterlectures_2021 = SemesterLectureFactory.create(
            semester=cls.semester_2021,
            lectures=cls.lectures_2016,
            recognized_majors=[cls.major]*5
        )


    def test_semester_retrieve(self):
        """
        Test [GET] semester/<semester_id>/
        """

        # semester retrieve
        response = self.client.get(
            f"/semester/{self.semester_2016.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['id'], self.semester_2016.id)
        self.assertEqual(data['plan'], self.plan.id)
        self.assertEqual(data['year'], self.semester_2016.year)
        self.assertEqual(data['semester_type'], self.semester_2016.semester_type)
        self.assertEqual(data['major_requirement_credit'], self.semester_2016.major_requirement_credit)
        self.assertEqual(data['major_elective_credit'], self.semester_2016.major_elective_credit)
        self.assertEqual(data['general_credit'], self.semester_2016.general_credit)
        self.assertEqual(data['general_elective_credit'], self.semester_2016.general_elective_credit)

        for i, lecture in enumerate(data['lectures']):
            self.assertEqual(lecture['lecture_name'], self.lectures_list_2016[i])

        # semester retrieve 404 error
        response = self.client.get(
            "/semester/9999/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_semester_delete(self):
        """
        Test [DELETE] semester/<semester_id>/
        """

        # semester delete
        response = self.client.delete(
            f"/semester/{self.semester_2021.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        semester_2021 = Semester.objects.filter(plan=self.plan, year=2021, semester_type='first').exists()
        self.assertEqual(semester_2021, False)

    
    def test_semester_update(self):
        """
        Test [PUT] semester/<semester_id>/
        """

        body = {
            "year": 2019,
            "semester_type": "second"
        }

        # semester update
        response = self.client.put(
            f"/semester/{self.semester_2016.id}/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['id'], self.semester_2016.id)
        self.assertEqual(data['plan'], self.plan.id)
        self.assertEqual(data['year'], 2019)
        self.assertEqual(data['semester_type'], "second")
        self.assertEqual(data['major_requirement_credit'], self.semester_2016.major_requirement_credit)
        self.assertEqual(data['major_elective_credit'], self.semester_2016.major_elective_credit)
        self.assertEqual(data['general_credit'], self.semester_2016.general_credit)
        self.assertEqual(data['general_elective_credit'], self.semester_2016.general_elective_credit)

        for i, lecture in enumerate(data['lectures']):
            self.assertEqual(lecture['lecture_name'], self.lectures_list_2016[i])

        # semester update 403 errors
        body = {}
        response = self.client.put(
            f"/semester/{self.semester_2016.id}/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data["error"], "body is empty")

        body = {
            "year": 2021,
            "semester_type": "second"
        }
        response = self.client.put(
            f"/semester/{self.semester_2016.id}/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data["error"], "semester already_exist")

        # semester partial update
        body = {
            "year": 2016,
        }

        # semester update
        response = self.client.put(
            f"/semester/{self.semester_2016.id}/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['id'], self.semester_2016.id)
        self.assertEqual(data['plan'], self.plan.id)
        self.assertEqual(data['year'], 2016)
        self.assertEqual(data['semester_type'], "second")

        body = {
            "semester_type":"first"
        }

        # semester update
        response = self.client.put(
            f"/semester/{self.semester_2016.id}/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['id'], self.semester_2016.id)
        self.assertEqual(data['plan'], self.plan.id)
        self.assertEqual(data['year'], 2016)
        self.assertEqual(data['semester_type'], "first")


class PlanTestCase(TestCase):
    """
    # Test

    [GET] plan/
    [GET] plan/<plan_id>/
    [DELETE] plan/<plan_id>/
    [PUT] plan/<plan_id>/
    [POST] plan/<plan_id>/copy/
    [PUT] plan/<plan_id>/major/
    """

    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory.create()
        cls.user_token = "Token " + str(cls.user.auth_token)
        
        cls.plan_1 = Plan.objects.create(user=cls.user, plan_name="test_1")

        cls.p1_semesters = SemesterFactory.create(
            semesters=[
                {
                    "plan":cls.plan_1,
                    "year":2016,
                    "semester_type":"first",
                    "major_requirement_credit":3,
                    "major_elective_credit":6
                },
                {
                    "plan":cls.plan_1,
                    "year":2016,
                    "semester_type":"second",
                    "major_requirement_credit":6,
                    "major_elective_credit":3

                }
            ]
        )

        cls.p1_semester_1 = Semester.objects.get(year=2016, semester_type="first")
        cls.p1_semester_2 = Semester.objects.get(year=2016, semester_type="second")
        cls.major_1 = Major.objects.get(major_name="경영학과", major_type="major")
        cls.p1_planmajor = PlanMajor.objects.create(major=cls.major_1, plan=cls.plan_1)
        cls.p1_lectures_1 = [
            "디자인 사고와 혁신", 
            "고급회계",
            "국제경영"
        ]
        cls.p1_lectures_2 = [
            "경영과학",
            "회계원리",
            "고급회계",
        ]
        cls.p1_lecture_instances_1 = Lecture.objects.filter(lecture_name__in=cls.p1_lectures_1)
        cls.p1_lecture_instances_2 = Lecture.objects.filter(lecture_name__in=cls.p1_lectures_2)

        cls.p1_semesterlectures_1 = SemesterLectureFactory.create(
            semester=cls.p1_semester_1,
            lectures=cls.p1_lecture_instances_1,
            recognized_majors=[cls.major_1]*3
        )
        cls.p1_semesterlectures_2 = SemesterLectureFactory.create(
            semester=cls.p1_semester_2,
            lectures=cls.p1_lecture_instances_2,
            recognized_majors=[cls.major_1]*3
        )

        cls.plan_2 = Plan.objects.create(user=cls.user, plan_name="test_2")

        cls.p2_semesters = SemesterFactory.create(
            semesters=[
                {
                    "plan":cls.plan_2,
                    "year":2017,
                    "semester_type":"first",
                    "major_requirement_credit":3,
                    "major_elective_credit":0
                },
                {
                    "plan":cls.plan_2,
                    "year":2017,
                    "semester_type":"second",
                    "major_requirement_credit":0,
                    "major_elective_credit":3

                }
            ]
        )

        cls.p2_semester_1 = Semester.objects.get(year=2017, semester_type="first")
        cls.p2_semester_2 = Semester.objects.get(year=2017, semester_type="second")

        cls.major_2 = Major.objects.get(major_name="컴퓨터공학부", major_type="double_major")

        cls.p2_planmajor_1 = PlanMajor.objects.create(major=cls.major_1, plan=cls.plan_2)
        cls.p2_planmajor_2 = PlanMajor.objects.create(major=cls.major_2, plan=cls.plan_2)
        cls.p2_lectures_1 = [
            "경영학원론"
        ]
        cls.p2_lectures_2 = [
            "국제경영"
        ]
        cls.p2_lecture_instances_1 = Lecture.objects.filter(lecture_name__in=cls.p2_lectures_1)
        cls.p2_lecture_instances_2 = Lecture.objects.filter(lecture_name__in=cls.p2_lectures_2)

        cls.p2_semesterlectures_1 = SemesterLectureFactory.create(
            semester=cls.p2_semester_1,
            lectures=cls.p2_lecture_instances_1,
            recognized_majors=[cls.major_1]
        )
        cls.p2_semesterlectures_2 = SemesterLectureFactory.create(
            semester=cls.p2_semester_2,
            lectures=cls.p2_lecture_instances_2,
            recognized_majors=[cls.major_1]
        )

        cls.plan_deleted = Plan.objects.create(user=cls.user, plan_name="test_deleted")

    def test_plan_list(self):
        """
        Test [GET] plan/
        """

        response = self.client.get(
            "/plan/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data), 3)

        plan_1 = data[0]
        self.assertEqual(plan_1['plan_name'], self.plan_1.plan_name)
        self.assertEqual(len(plan_1['majors']), 1)
        self.assertEqual(plan_1['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(plan_1['majors'][0]['major_type'], self.major_1.major_type)
        
        self.assertEqual(len(plan_1['semesters']), 2)
        self.assertEqual(plan_1['semesters'][0]['year'], self.p1_semester_1.year)
        self.assertEqual(plan_1['semesters'][0]['semester_type'], self.p1_semester_1.semester_type)
        self.assertEqual(plan_1['semesters'][0]['major_requirement_credit'], self.p1_semester_1.major_requirement_credit)
        self.assertEqual(plan_1['semesters'][0]['major_elective_credit'], self.p1_semester_1.major_elective_credit)
        self.assertEqual(len(plan_1['semesters'][0]['lectures']), 3)

        self.assertEqual(plan_1['semesters'][1]['year'], self.p1_semester_2.year)
        self.assertEqual(plan_1['semesters'][1]['semester_type'], self.p1_semester_2.semester_type)
        self.assertEqual(plan_1['semesters'][1]['major_requirement_credit'], self.p1_semester_2.major_requirement_credit)
        self.assertEqual(plan_1['semesters'][1]['major_elective_credit'], self.p1_semester_2.major_elective_credit)
        self.assertEqual(len(plan_1['semesters'][1]['lectures']), 3)

        plan_2 = data[1]
        self.assertEqual(plan_2['plan_name'], self.plan_2.plan_name)
        self.assertEqual(len(plan_2['majors']), 2)
        self.assertEqual(plan_2['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(plan_2['majors'][0]['major_type'], self.major_1.major_type)
        self.assertEqual(plan_2['majors'][1]['major_name'], self.major_2.major_name)
        self.assertEqual(plan_2['majors'][1]['major_type'], self.major_2.major_type)
        
        self.assertEqual(len(plan_2['semesters']), 2)
        self.assertEqual(plan_2['semesters'][0]['year'], self.p2_semester_1.year)
        self.assertEqual(plan_2['semesters'][0]['semester_type'], self.p2_semester_1.semester_type)
        self.assertEqual(plan_2['semesters'][0]['major_requirement_credit'], self.p2_semester_1.major_requirement_credit)
        self.assertEqual(plan_2['semesters'][0]['major_elective_credit'], self.p2_semester_1.major_elective_credit)
        self.assertEqual(len(plan_2['semesters'][0]['lectures']), 1)

        self.assertEqual(plan_2['semesters'][1]['year'], self.p2_semester_2.year)
        self.assertEqual(plan_2['semesters'][1]['semester_type'], self.p2_semester_2.semester_type)
        self.assertEqual(plan_2['semesters'][1]['major_requirement_credit'], self.p2_semester_2.major_requirement_credit)
        self.assertEqual(plan_2['semesters'][1]['major_elective_credit'], self.p2_semester_2.major_elective_credit)
        self.assertEqual(len(plan_2['semesters'][1]['lectures']), 1)

   
    def test_plan_retrieve(self):
        """
        Test [GET] plan/<plan_id>/
        """

        response = self.client.get(
            f"/plan/{self.plan_1.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['plan_name'], self.plan_1.plan_name)
        self.assertEqual(len(data['majors']), 1)
        self.assertEqual(data['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(data['majors'][0]['major_type'], self.major_1.major_type)
        
        self.assertEqual(len(data['semesters']), 2)
        self.assertEqual(data['semesters'][0]['year'], self.p1_semester_1.year)
        self.assertEqual(data['semesters'][0]['semester_type'], self.p1_semester_1.semester_type)
        self.assertEqual(data['semesters'][0]['major_requirement_credit'], self.p1_semester_1.major_requirement_credit)
        self.assertEqual(data['semesters'][0]['major_elective_credit'], self.p1_semester_1.major_elective_credit)
        self.assertEqual(len(data['semesters'][0]['lectures']), 3)

        self.assertEqual(data['semesters'][1]['year'], self.p1_semester_2.year)
        self.assertEqual(data['semesters'][1]['semester_type'], self.p1_semester_2.semester_type)
        self.assertEqual(data['semesters'][1]['major_requirement_credit'], self.p1_semester_2.major_requirement_credit)
        self.assertEqual(data['semesters'][1]['major_elective_credit'], self.p1_semester_2.major_elective_credit)
        self.assertEqual(len(data['semesters'][1]['lectures']), 3)


    def test_plan_delete(self):
        """
        Test [DELETE] plan/<plan_id>/
        """

        response = self.client.delete(
            f"/plan/{self.plan_deleted.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.plan.filter(plan_name="test_deleted").exists(), False)


    def test_plan_update(self):
        """
        Test [PUT] plan/<plan_id>/
        """

        response = self.client.put(
            f"/plan/{self.plan_2.id}/",
            data={
                "plan_name": "test_2_modified"
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['plan_name'], "test_2_modified")

        response = self.client.put(
            f"/plan/{self.plan_2.id}/",
            data={
                "plan_name": "test_2"
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['plan_name'], "test_2")


    def test_plan_copy(self):
        """
        Test [POST] plan/<plan_id>/copy/
        """

        response = self.client.post(
            f"/plan/{self.plan_2.id}/copy/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['plan_name'], f"{self.plan_2.plan_name} (복사본)")

        self.assertEqual(len(data['majors']), 2)
        self.assertEqual(data['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(data['majors'][0]['major_type'], self.major_1.major_type)
        self.assertEqual(data['majors'][1]['major_name'], self.major_2.major_name)
        self.assertEqual(data['majors'][1]['major_type'], self.major_2.major_type)
        
        self.assertEqual(len(data['semesters']), 2)
        self.assertEqual(data['semesters'][0]['year'], self.p2_semester_1.year)
        self.assertEqual(data['semesters'][0]['semester_type'], self.p2_semester_1.semester_type)
        self.assertEqual(data['semesters'][0]['major_requirement_credit'], self.p2_semester_1.major_requirement_credit)
        self.assertEqual(data['semesters'][0]['major_elective_credit'], self.p2_semester_1.major_elective_credit)
        self.assertEqual(len(data['semesters'][0]['lectures']), 1)

        self.assertEqual(data['semesters'][1]['year'], self.p2_semester_2.year)
        self.assertEqual(data['semesters'][1]['semester_type'], self.p2_semester_2.semester_type)
        self.assertEqual(data['semesters'][1]['major_requirement_credit'], self.p2_semester_2.major_requirement_credit)
        self.assertEqual(data['semesters'][1]['major_elective_credit'], self.p2_semester_2.major_elective_credit)
        self.assertEqual(len(data['semesters'][1]['lectures']), 1)

    
    def test_plan_major_update(self):
        """
        Test [PUT] plan/<plan_id>/major/
        """

        pass