from django.contrib.auth.models import User
from django.db import models
from user.models import Major


# Lecture, Plan, Semester, PlanMajor, SemesterLecture, MajorLecture
class Lecture(models.Model):
    UNKNOWN = 'unknown'
    FIRST = 'first'
    SECOND = 'second'
    SUMMER = 'summer'
    WINTER = 'winter'
    ALL = 'all'

    SEMESTER_TYPE = (
        (UNKNOWN, 'unknown'),
        (FIRST, 'first'),
        (SECOND, 'second'),
        (SUMMER, 'summer'),
        (WINTER, 'winter'),
        (ALL, 'all'),
    )
    lecture_id = models.CharField(max_length=50, default="")
    lecture_name = models.CharField(max_length=50, db_index=True)
    open_department = models.CharField(max_length=50, null=True)
    open_major = models.CharField(max_length=50, null=True)
    open_semester = models.CharField(max_length=50, choices=SEMESTER_TYPE, default=UNKNOWN)
    credit = models.PositiveIntegerField(default=0)
    grade = models.PositiveSmallIntegerField(null=True)
    prev_lecture_id = models.CharField(max_length=50, null=True)


class Plan(models.Model):
    user = models.ForeignKey(User, related_name='plan', on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=50, db_index=True, default="새로운 계획")
    recent_scroll = models.IntegerField(default=0)


class Semester(models.Model):
    FIRST = 'first'
    SECOND = 'second'
    SUMMER = 'summer'
    WINTER = 'winter'

    SEMESTER_TYPE = (
        (FIRST, 'first'),
        (SECOND, 'second'),
        (SUMMER, 'summer'),
        (WINTER, 'winter'),
    )
    plan = models.ForeignKey(Plan, related_name='semester', on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    semester_type = models.CharField(max_length=50, choices=SEMESTER_TYPE)
    is_complete = models.BooleanField(default=False)
    major_requirement_credit = models.PositiveSmallIntegerField(default=0)
    major_elective_credit = models.PositiveSmallIntegerField(default=0)
    general_credit = models.PositiveSmallIntegerField(default=0)
    general_elective_credit = models.PositiveSmallIntegerField(default=0)



class PlanMajor(models.Model):
    plan = models.ForeignKey(Plan, related_name='planmajor', on_delete=models.CASCADE)
    major = models.ForeignKey(Major, related_name='planmajor', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('plan', 'major')
        )


class SemesterLecture(models.Model):
    # 공통
    NONE = 'none'  # 구분 없음

    # Lecture Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
    GENERAL = 'general'  # 일반 선택
    GENERAL_ELECTIVE = 'general_elective'  # 교양
    TEACHING = 'teaching'  # 교직

    # Lecture Type Detail
    BASE_OF_STUDY = 'base_of_study'  # 학문의 기초
    WORLD_OF_STUDY = 'world_of_study'  # 학문의 세계
    OTHER = 'other'  # 일반 교양

    # Lecture Type Detail Detail
    THOUGHT_AND_EXPRESSION = 'thought_and_expression'  # 사고와 표현
    FOREIGN_LANGUAGES = 'foreign_languages'  # 외국어
    MATHEMATICAL_ANALYSIS_AND_REASONING = 'mathematical_analysis_and_reasoning'  # 수량적 분석과 추론
    SCIENTIFIC_THINKING_AND_EXPERIMENT = 'scientific_thinking_and_experiment'  # 과학적 사고와 실험
    COMPUTER_AND_INFORMATICS = 'computer_and_informatics'  # 컴퓨터와 정보활용
    LANGUAGE_AND_LITERATURE = 'language_and_literature'  # 언어와 문학
    CULTURE_AND_ARTS = 'culture_and_arts'  # 문화와 예술
    HISTORY_AND_PHILOSOPHY = 'history_and_philosophy'  # 역사와 철학
    POLITICS_AND_ECONOMICS = 'politics_and_economics'  # 정치와 경제
    HUMANITY_AND_SOCIETY = 'humanity_and_society'  # 인간과 사회
    NATURE_AND_TECHNOLOGY = 'nature_and_technology'  # 자연과 기술
    LIFE_AND_ENVIRONMENT = 'life_and_environment'  # 생명과 환경

    LECTURE_TYPE = (
        (NONE, 'none'),
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ELECTIVE, 'major_elective'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching'),
    )
    LECTURE_TYPE_DETAIL = (
        (NONE, 'none'),
        (BASE_OF_STUDY, 'base_of_study'),
        (WORLD_OF_STUDY, 'world_of_study'),
        (OTHER, 'other'),
    )
    LECTURE_TYPE_DETAIL_DETAIL = (
        (NONE, 'none'),  # 구분 없음
        (THOUGHT_AND_EXPRESSION, 'thought_and_expression'),  # 사고와 표현
        (FOREIGN_LANGUAGES, 'foreign_languages'),  # 외국어
        (MATHEMATICAL_ANALYSIS_AND_REASONING, 'mathematical_analysis_and_reasoning'),  # 수량적 분석과 추론
        (SCIENTIFIC_THINKING_AND_EXPERIMENT, 'scientific_thinking_and_experiment'),  # 과학적 사고와 실험
        (COMPUTER_AND_INFORMATICS, 'computer_and_informatics'),  # 컴퓨터와 정보활용
        (LANGUAGE_AND_LITERATURE, 'language_and_literature'),  # 언어와 문학
        (CULTURE_AND_ARTS, 'culture_and_arts'),  # 문화와 예술
        (HISTORY_AND_PHILOSOPHY, 'history_and_philosophy'),  # 역사와 철학
        (POLITICS_AND_ECONOMICS, 'politics_and_economics'),  # 정치와 경제
        (HUMANITY_AND_SOCIETY, 'humanity_and_society'),  # 인간과 사회
        (NATURE_AND_TECHNOLOGY, 'nature_and_technology'),  # 자연과 기술
        (LIFE_AND_ENVIRONMENT, 'life_and_environment'),  # 생명과 환경
    )
    semester = models.ForeignKey(Semester, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='semesterlecture', on_delete=models.CASCADE)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE)
    lecture_type_detail = models.CharField(max_length=50, choices=LECTURE_TYPE_DETAIL, default=NONE)
    lecture_type_detail_detail = models.CharField(max_length=50, choices=LECTURE_TYPE_DETAIL_DETAIL, default=NONE)
    recent_sequence = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (
            ('semester', 'lecture')
        )


class MajorLecture(models.Model):
    # 공통
    NONE = 'none'  # 구분 없음

    # Lecture Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
    GENERAL = 'general'  # 일반 선택
    GENERAL_ELECTIVE = 'general_elective'  # 교양
    TEACHING = 'teaching'  # 교직

    # Lecture Type Detail
    BASE_OF_STUDY = 'base_of_study'  # 학문의 기초
    WORLD_OF_STUDY = 'world_of_study'  # 학문의 세계
    OTHER = 'other'  # 일반 교양

    # Lecture Type Detail Detail
    THOUGHT_AND_EXPRESSION = 'thought_and_expression'  # 사고와 표현
    FOREIGN_LANGUAGES = 'foreign_languages'  # 외국어
    MATHEMATICAL_ANALYSIS_AND_REASONING = 'mathematical_analysis_and_reasoning'  # 수량적 분석과 추론
    SCIENTIFIC_THINKING_AND_EXPERIMENT = 'scientific_thinking_and_experiment'  # 과학적 사고와 실험
    COMPUTER_AND_INFORMATICS = 'computer_and_informatics'  # 컴퓨터와 정보활용
    LANGUAGE_AND_LITERATURE = 'language_and_literature'  # 언어와 문학
    CULTURE_AND_ARTS = 'culture_and_arts'  # 문화와 예술
    HISTORY_AND_PHILOSOPHY = 'history_and_philosophy'  # 역사와 철학
    POLITICS_AND_ECONOMICS = 'politics_and_economics'  # 정치와 경제
    HUMANITY_AND_SOCIETY = 'humanity_and_society'  # 인간과 사회
    NATURE_AND_TECHNOLOGY = 'nature_and_technology'  # 자연과 기술
    LIFE_AND_ENVIRONMENT = 'life_and_environment'  # 생명과 환경

    LECTURE_TYPE = (
        (NONE, 'none'),
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ELECTIVE, 'major_elective'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching')
    )
    LECTURE_TYPE_DETAIL = (
        (NONE, 'none'),
        (BASE_OF_STUDY, 'base_of_study'),
        (WORLD_OF_STUDY, 'world_of_study'),
        (OTHER, 'other'),
    )
    LECTURE_TYPE_DETAIL_DETAIL = (
        (NONE, 'none'),  # 구분 없음
        (THOUGHT_AND_EXPRESSION, 'thought_and_expression'),  # 사고와 표현
        (FOREIGN_LANGUAGES, 'foreign_languages'),  # 외국어
        (MATHEMATICAL_ANALYSIS_AND_REASONING, 'mathematical_analysis_and_reasoning'),  # 수량적 분석과 추론
        (SCIENTIFIC_THINKING_AND_EXPERIMENT, 'scientific_thinking_and_experiment'),  # 과학적 사고와 실험
        (COMPUTER_AND_INFORMATICS, 'computer_and_informatics'),  # 컴퓨터와 정보활용
        (LANGUAGE_AND_LITERATURE, 'language_and_literature'),  # 언어와 문학
        (CULTURE_AND_ARTS, 'culture_and_arts'),  # 문화와 예술
        (HISTORY_AND_PHILOSOPHY, 'history_and_philosophy'),  # 역사와 철학
        (POLITICS_AND_ECONOMICS, 'politics_and_economics'),  # 정치와 경제
        (HUMANITY_AND_SOCIETY, 'humanity_and_society'),  # 인간과 사회
        (NATURE_AND_TECHNOLOGY, 'nature_and_technology'),  # 자연과 기술
        (LIFE_AND_ENVIRONMENT, 'life_and_environment'),  # 생명과 환경
    )
    major = models.ForeignKey(Major, related_name='majorlecture', on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, related_name='majorlecture', on_delete=models.CASCADE)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    is_required = models.BooleanField(default=False)
    lecture_type = models.CharField(max_length=50, choices=LECTURE_TYPE)
    lecture_type_detail = models.CharField(max_length=50, choices=LECTURE_TYPE_DETAIL, default=NONE)
    lecture_type_detail_detail = models.CharField(max_length=50, choices=LECTURE_TYPE_DETAIL_DETAIL, default=NONE)

    class Meta:
        unique_together = (
            ('major', 'lecture')
        )
