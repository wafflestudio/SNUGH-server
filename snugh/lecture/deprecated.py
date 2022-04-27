"""
# Data Generation
    # POST /lecture/generate_lecturecredit/
    @action(methods=['POST'], detail=False)
    @transaction.atomic
    def generate_lecturecredit(self, request):
        lectures = Lecture.objects.all()
        id_cnt = 0 # 이전 item의 id
        for lecture in lectures:
            lecture_code = lecture.lecture_code
            lecturecredits = LectureTmp.objects.filter(lecture_code=lecture_code).order_by('id')
            if lecturecredits.count() == 0:
                return Response({"error": "lecture missing"}, status=status.HTTP_400_BAD_REQUEST)
            elif lecturecredits.count() == 1:
                LectureCredit.objects.create(lecture=lecture,
                                             credit=lecturecredits.first().credit,
                                             start_year=lecturecredits.first().open_year,
                                             end_year = 10000)
                id_cnt+=1
            else:
                cnt = 0
                for lecturecredit in lecturecredits:
                    LectureCredit.objects.create(lecture=lecture,
                                                 credit=lecturecredit.credit,
                                                 start_year=lecturecredit.open_year,
                                                 end_year=10000)
                    if cnt !=0:
                        prev_lecturecredit = LectureCredit.objects.get(id=id_cnt)
                        prev_lecturecredit.end_year = lecturecredit.open_year -1
                        prev_lecturecredit.save()
                    cnt +=1
                    id_cnt+=1
        return Response(status=status.HTTP_200_OK)

    # POST /lecture/combine_majorlecture/
    # 수집된 데이터와 수강신청 사이트의 데이터 합치기(수강신청 사이트 데이터에 없는 강의만 추가)
    @action(methods=['POST'], detail=False)
    @transaction.atomic
    def combine_majorlecture(self, request):
        cnt_created=0
        majors = Major.objects.exclude(major_type = Major.SINGLE_MAJOR).exclude(major_type=Major.DOUBLE_MAJOR).exclude(major_type=Major.MINOR)
        for major in majors:
            majorlectures_auto_lectures = LectureTmp.objects.filter(open_major=major.major_name).values_list('lecture_code', flat=True).distinct()
            majorlectures_collected = MajorLectureTmp.objects.filter(major_name=major.major_name)
            for ml in majorlectures_collected:
                if ml.lecture_code not in majorlectures_auto_lectures:
                    LectureTmp.objects.create(lecture_code=ml.lecture_code,
                                              lecture_name='',
                                              open_major=ml.major_name,
                                              open_year=ml.start_year,
                                              lecture_type=ml.lecture_type,
                                              is_added=True)
                    cnt_created+=1
        return Response(cnt_created, status=status.HTTP_200_OK)


    # POST /lecture/generate_majorlecture/
    @action(methods=['POST'], detail=False)
    @transaction.atomic
    def generate_majorlecture(self, request):
        created_cnt = 0
        deleted_cnt = 0
        auto_generated_cnt = 0
        # generate majorlecture object from lecturetmp, find start_year, end_year
        majors = Major.objects.all()
        id_cnt = 0
        for major in majors:
            open_department = Department.objects.get(majordepartment__major = major).department_name
            if major.major_name == 'none':
                majorlectures_lecture_codes = LectureTmp.objects.filter(open_major=major.major_name).values_list('lecture_code', flat=True).distinct()
            else:
                majorlectures_lecture_codes = LectureTmp.objects.filter(open_major=major.major_name, open_department=open_department).values_list('lecture_code', flat=True).distinct()
            for lecture_code in majorlectures_lecture_codes:
                if major.major_name == 'none':
                    majorlectures = LectureTmp.objects.filter(open_major=major.major_name,
                                                              lecture_code=lecture_code).order_by('id')
                else:
                    majorlectures = LectureTmp.objects.filter(open_major = major.major_name, open_department=open_department, lecture_code = lecture_code).order_by('id')
                if majorlectures.count() == 0:
                    return Response({"error": "missing"}, status=status.HTTP_400_BAD_REQUEST)
                elif majorlectures.count() == 1:
                    MajorLecture.objects.create(major = major,
                                                lecture = Lecture.objects.get(lecture_code = lecture_code),
                                                start_year = majorlectures.first().open_year,
                                                end_year = 10000,
                                                lecture_type = majorlectures.first().lecture_type)
                    id_cnt += 1;
                else:
                    cnt = 0
                    for majorlecture in majorlectures:
                        MajorLecture.objects.create(major=major,
                                                    lecture=Lecture.objects.get(lecture_code=lecture_code),
                                                    start_year=majorlecture.open_year,
                                                    end_year=10000,
                                                    lecture_type=majorlecture.lecture_type)
                        if cnt != 0:
                            prev_majorlecture = MajorLecture.objects.get(id=id_cnt)
                            if prev_majorlecture.start_year == majorlecture.open_year:
                                prev_majorlecture.end_year = majorlecture.open_year
                            else:
                                prev_majorlecture.end_year = majorlecture.open_year - 1
                            prev_majorlecture.save()
                        cnt += 1
                        id_cnt += 1
        created_cnt = id_cnt

        # generate majorlecture object for major = none, lecture_type = 'major_requirement' or 'major_elective'
        null_majorlectures = MajorLecture.objects.filter(major = Major.objects.get(major_name = 'none'), lecture_type = Lecture.MAJOR_REQUIREMENT)|MajorLecture.objects.filter(major = Major.objects.get(major_name = 'none'), lecture_type = Lecture.MAJOR_ELECTIVE)
        for null_majorlecture in null_majorlectures:
            null_majorlecture_src = LectureTmp.objects.get(open_major = null_majorlecture.major.major_name, lecture_code= null_majorlecture.lecture.lecture_code, open_year = null_majorlecture.start_year, lecture_type = null_majorlecture.lecture_type)
            open_department = Department.objects.get(department_name=null_majorlecture_src.open_department)
            majors = Major.objects.filter(majordepartment__department=open_department)
            for major in majors:
                existing_majorlectures = MajorLecture.objects.filter(major = major, lecture = null_majorlecture.lecture)
                if existing_majorlectures.count() == 0:
                    MajorLecture.objects.create(major=major,
                                                lecture=null_majorlecture.lecture,
                                                start_year=null_majorlecture.start_year,
                                                end_year=null_majorlecture.end_year,
                                                lecture_type=null_majorlecture.lecture_type)
                    auto_generated_cnt += 1
            null_majorlecture.delete()
            deleted_cnt += 1

        data = [created_cnt, deleted_cnt, auto_generated_cnt]
        return Response(data, status=status.HTTP_200_OK)
"""
