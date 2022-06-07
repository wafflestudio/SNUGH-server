from core.major.models import Major
from user.utils import UserFactory
from core.major.utils import UserMajorFactory
from django.db.models import Q
from django.test import TestCase
from rest_framework import status


class UserMajorTestCase(TestCase):
    """
    # Test Major APIs.

    [GET] major/
    [POST] user/major/
    [DELETE] user/major/
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.auto_create()
        cls.user_token = "Token " + str(cls.user.auth_token)
    
    def test_major_list(self):
        """
        Test cases in listing majors.
            1) no major_type and search_keyword returns all majors.
            2) both major_type and search_keyword exists.
            3) only search_keyword exists.
            4) only major_type exists.
        """

        # 중복여부, 정렬여부, None여부 확인 가능
        # None 값 제거 (-1)
        all_majors_cnt = Major.objects.values("major_name").distinct().count()-1

        # 1) no major_type and search_keyword returns all majors.
        body = {}
        response = self.client.get(
            "/major/",
            data=body,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data["majors"]), all_majors_cnt)

        for i in range(5):
            self.assertEqual((data["majors"][i]<=data["majors"][i+1]), True)
            self.assertEqual((data["majors"][-i-2]<=data["majors"][-i-1]), True)
        

        # 2) both major_type and search_keyword exists.
        body = {
            "major_type": "interdisciplinary_major",
            "search_keyword": "경영",
        }

        response = self.client.get(
            "/major/",
            data=body,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        results = [
            "글로벌환경경영학",
            "기술경영",
            "벤처경영학"
        ]

        self.assertEqual(len(data["majors"]), len(results))

        for idx, major_name in enumerate(results):
            self.assertEqual(data["majors"][idx], major_name)

        # 3) only search_keyword exists.
        body = {"search_keyword": "경영"}
        response = self.client.get(
            "/major/",
            data=body,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        results = [
            "경영학과",
            "글로벌환경경영학",
            "기술경영",
            "벤처경영학",
            "협동과정 기술경영·경제·정책전공",
            "협동과정 미술경영"
        ]

        self.assertEqual(len(data["majors"]), len(results))

        for idx, major_name in enumerate(results):
            self.assertEqual(data["majors"][idx], major_name)

        # 4) only major_type exists.
        body = {
            "major_type": "interdisciplinary_major",
        }
        response = self.client.get(
            "/major/",
            data=body,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        results = [
            "계산과학",
            "글로벌환경경영학",
            "기술경영",
            "동아시아비교인문학",
            "벤처경영학",
            "영상매체예술",
            "인공지능",
            "인공지능반도체공학",
            "정보문화학"
        ]

        self.assertEqual(len(data["majors"]), len(results))

        for idx, major_name in enumerate(results):
            self.assertEqual(data["majors"][idx], major_name)


    def test_major_create(self):
        """
        Test cases in creating user majors.
        """

        body = {"major_type": "major", "major_name": "경영학과"}
        response = self.client.post(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data["majors"][0]["major_name"], "경영학과")
        self.assertEqual(data["majors"][0]["major_type"], "major")

        body = {"major_type": "single_major", "major_name": "컴퓨터공학부"}
        response = self.client.post(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data["majors"][0]["major_name"], "경영학과")
        self.assertEqual(data["majors"][0]["major_type"], "major")
        self.assertEqual(data["majors"][1]["major_name"], "컴퓨터공학부")
        self.assertEqual(data["majors"][1]["major_type"], "major")

        body = {"major_type": "interdisciplinary_major", "major_name": "인공지능"}
        response = self.client.post(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data["majors"][0]["major_name"], "경영학과")
        self.assertEqual(data["majors"][0]["major_type"], "major")
        self.assertEqual(data["majors"][1]["major_name"], "컴퓨터공학부")
        self.assertEqual(data["majors"][1]["major_type"], "major")
        self.assertEqual(data["majors"][2]["major_name"], "인공지능")
        self.assertEqual(data["majors"][2]["major_type"], "interdisciplinary_major")

        usermajors = self.user.usermajor.select_related("major").all()
        self.assertEqual(
            usermajors.filter(
                major__major_name="경영학과", major__major_type="major"
            ).exists(),
            True,
        )
        self.assertEqual(
            usermajors.filter(
                major__major_name="컴퓨터공학부", major__major_type="major"
            ).exists(),
            True,
        )
        self.assertEqual(
            usermajors.filter(
                major__major_name="인공지능", major__major_type="interdisciplinary_major"
            ).exists(),
            True,
        )


    def test_major_create_error(self):
        """
        Error cases in creating user majors.
            1) major does not exist.
            2) major already exists.
        """

        # 1) major does not exist.
        body = {"major_type": "major", "major_name": "샤프심학과"}
        response = self.client.post(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["error"], "major not_exist")

        # 2) major already exists.
        body = {"major_type": "major", "major_name": "경영학과"}
        response = self.client.post(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = {"major_type": "double_major", "major_name": "경영학과"}
        response = self.client.post(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["error"], "major already_exist")


    def test_major_delete(self):
        """
        Test cases in deleting user majors.
        """

        UserMajorFactory.create(
            user=self.user,
            majors=Major.objects.filter(
                (Q(major_name="경영학과") | Q(major_name="컴퓨터공학부")) & Q(major_type="major")
            ),
        )

        body = {"major_type": "major", "major_name": "컴퓨터공학부"}
        response = self.client.delete(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(len(data["majors"]), 1)
        self.assertEqual(data["majors"][0]["major_name"], "경영학과")
        self.assertEqual(data["majors"][0]["major_type"], "single_major")

        usermajors = self.user.usermajor.select_related("major").all()
        self.assertEqual(
            usermajors.filter(
                major__major_name="경영학과", major__major_type="major"
            ).exists(),
            False,
        )
        self.assertEqual(
            usermajors.filter(
                major__major_name="경영학과", major__major_type="single_major"
            ).exists(),
            True,
        )


    def test_major_delete_error(self):
        """
        Error cases in deleting user majors.
            1) major does not exist.
            2) usermajor does not exist.
            3) userMajor cannot be zero or minus.
        """

        UserMajorFactory.create(
            user=self.user,
            majors=Major.objects.filter(Q(major_name="경영학과") & Q(major_type="major")),
        )

        # 1) major does not exist.
        body = {"major_type": "major", "major_name": "샤프심학과"}
        response = self.client.delete(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["error"], "major not_exist")

        # 2) usermajor does not exist.
        body = {"major_type": "major", "major_name": "컴퓨터공학부"}
        response = self.client.delete(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["error"], "usermajor not_exist")

        # 3) userMajor cannot be zero or minus.
        body = {"major_type": "major", "major_name": "경영학과"}
        response = self.client.delete(
            "/user/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["error"], "The number of majors cannot be zero or minus.")
