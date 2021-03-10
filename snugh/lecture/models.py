from django.contrib.auth.models import User
from django.db import models
from user.models import Major

# Create your models here.
# Lecture, Plan, Semester, PlanMajor, SemesterLecture, MajorLecture 

class Lecture(models.Model):
    lecture_id = models.CharField(max_length=50, default="")
    SEMESTER_TYPE = (
        (1, 'unknown'),
        (2, 'first'),
        (3, 'second'),
        (4, 'summer'),
        (5, 'winter'),
    )
    lecture_name = models.CharField(max_length=50, db_index=True)
    credit = models.PositiveIntegerField(default=0)
    is_open = models.BooleanField(default=False)
    open_semester = models.PositiveSmallIntegerField(choices=SEMESTER_TYPE, default=1)

class Plan(models.Model):
    user = models.ForeignKey(User, related_name='plan', on_delete=models.CASCADE, null=True)
    plan_name = models.CharField(max_length=50, db_index=True, default="계획표")
    recent_scroll = models.IntegerField(default=0)

class Semester(models.Model):
    SEMESTER_TYPE = (
        (1, 'first'),
        (2, 'second'),
        (3, 'summer'),
        (4, 'winter'),
    )
    plan = models.ForeignKey(Plan, related_name='semester', on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    is_complete = models.BooleanField(default=False) 
    semester_type = models.PositiveSmallIntegerField(choices=SEMESTER_TYPE)

class PlanMajor(models.Model):
    plan = models.ForeignKey(Plan, related_name='planmajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='planmajor', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('plan', 'major')
        )

class SemesterLecture(models.Model):
    LECTURE_TYPE = (
        (1, 'general'), # 교양
        (2, 'major_requirement'), # 전공 필수
        (3, 'major_elective'), # 전공 선택
    )
    LECTURE_TYPE_DETAIL = (
        (1, 'none'), # 구분 없음
        (2, 'base_of_study'),  #  학문의 기초
        (3, 'world_of_study'),  # 학문의 세계
        (4, 'other'), # 일반교양
    )
    LECTURE_TYPE_DETAIL_DETAIL = (
        (1, 'none'),  # 구분 없음
        (2, 'thought_and_expression'),  # 사고와 표현
        (3, 'foreign_languages'),  # 외국어
        (4, 'mathematical_analysis_and_reasoning'), # 수량적 분석과 추론
        (5, 'scientific_thinking_and_experiment'), # 과학적 사고와 실험
        (6, 'computer and informatics'), # 컴퓨터와 정보활용
        (7, 'language and literature'), # 언어와 문학
        (8, 'culture and arts'), # 문화와 예술
        (9, 'history and philosophy'), # 역사와 철학
        (10, 'politics and economics'), # 정치와 경제
        (11, 'humanity and society'), # 인간과 사회
        (12, 'nature and technology'), # 자연과 기술
        (13, 'life and environment'), # 생명과 환경
    )
    semester = models.ForeignKey(Semester, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture_type = models.PositiveSmallIntegerField(choices=LECTURE_TYPE)
    lecture_type_detail = models.PositiveSmallIntegerField(choices=LECTURE_TYPE_DETAIL, default=1)
    lecture_type_detail_detail = models.PositiveSmallIntegerField(choices=LECTURE_TYPE_DETAIL_DETAIL, default = 1)
    recent_sequence = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (
            ('semester', 'lecture')
        )

class MajorLecture(models.Model):
    LECTURE_TYPE = (
        (1, 'general'),  # 교양
        (2, 'major_requirement'),  # 전공 필수
        (3, 'major_elective'),  # 전공 선택
    )
    LECTURE_TYPE_DETAIL = (
        (1, 'none'),  # 구분 없음
        (2, 'base_of_study'),  # 학문의 기초
        (3, 'world_of_study'),  # 학문의 세계
        (4, 'other'),  # 일반교양
    )
    LECTURE_TYPE_DETAIL_DETAIL = (
        (1, 'none'),  # 구분 없음
        (2, 'thought_and_expression'),  # 사고와 표현
        (3, 'foreign_languages'),  # 외국어
        (4, 'mathematical_analysis_and_reasoning'),  # 수량적 분석과 추론
        (5, 'scientific_thinking_and_experiment'),  # 과학적 사고와 실험
        (6, 'computer and informatics'),  # 컴퓨터와 정보활용
        (7, 'language and literature'),  # 언어와 문학
        (8, 'culture and arts'),  # 문화와 예술
        (9, 'history and philosophy'),  # 역사와 철학
        (10, 'politics and economics'),  # 정치와 경제
        (11, 'humanity and society'),  # 인간과 사회
        (12, 'nature and technology'),  # 자연과 기술
        (13, 'life and environment'),  # 생명과 환경
    )
    major = models.ForeignKey(Major, related_name='majorlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='majorlecture', on_delete=models.CASCADE)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    lecture_type = models.PositiveSmallIntegerField(choices=LECTURE_TYPE)
    lecture_type_detail = models.PositiveSmallIntegerField(choices=LECTURE_TYPE_DETAIL, default = 1)
    lecture_type_detail_detail = models.PositiveSmallIntegerField(choices=LECTURE_TYPE_DETAIL_DETAIL, default = 1)

    class Meta:
        unique_together = (
            ('major', 'lecture')
        )
