"""
@classmethod
    def setUpTestData(cls):

        cls.user = UserFactory.auto_create()
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


        cls.post_data = {
            "plan_name": "example plan",
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

        cls.put_data = {
            'email': 'testuser@test.com',
            'password': 'password',
        }
"""
"""
def test_plan_list(self):

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

        response = self.client.delete(
            f"/plan/{self.plan_deleted.id}/",
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.plan.filter(plan_name="test_deleted").exists(), False)


    def test_plan_update(self):


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

    # TODO: 아래 테스트 RequirementTest에서 활용하기
    def test_plan_major_update(self):
        # Test [PUT] plan/<plan_id>/major/

        # update major
        body = {
            "post_list": [{
                "major_name": "심리학과",
                "major_type": "double_major"
            }],
            "delete_list": [{
                "major_name": "컴퓨터공학부",
                "major_type": "double_major"
            }]
        }
        response = self.client.put(
            f"/plan/{self.plan_2.id}/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['plan_name'], self.plan_2.plan_name)
        self.assertEqual(len(data['majors']), 2)
        self.assertEqual(data['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(data['majors'][0]['major_type'], self.major_1.major_type)
        self.assertEqual(data['majors'][1]['major_name'], "심리학과")
        self.assertEqual(data['majors'][1]['major_type'], "double_major")
        
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

        # delete major
        body = {
            "delete_list": [{
                "major_name": "심리학과",
                "major_type": "double_major"
            }]
        }
        response = self.client.put(
            f"/plan/{self.plan_2.id}/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['plan_name'], self.plan_2.plan_name)
        self.assertEqual(len(data['majors']), 1)
        self.assertEqual(data['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(data['majors'][0]['major_type'], "single_major")

        # 400 error
        body = {
            "delete_list": [{
                "major_name": "경영학과",
                "major_type": "major"
            }]
        }
        response = self.client.put(
            f"/plan/{self.plan_2.id}/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['error'], "The number of majors cannot be zero or minus.")

        # add major
        body = {
            "post_list": [{
                "major_name": "컴퓨터공학부",
                "major_type": "double_major"
            }]
        }
        response = self.client.put(
            f"/plan/{self.plan_2.id}/major/",
            data=body,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['plan_name'], self.plan_2.plan_name)
        self.assertEqual(len(data['majors']), 2)
        self.assertEqual(data['majors'][0]['major_name'], self.major_1.major_name)
        self.assertEqual(data['majors'][0]['major_type'], "major")
        self.assertEqual(data['majors'][1]['major_name'], self.major_2.major_name)
        self.assertEqual(data['majors'][1]['major_type'], self.major_2.major_type)
"""
