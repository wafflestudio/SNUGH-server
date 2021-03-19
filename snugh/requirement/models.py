from django.db import models
from user.models import Major
from lecture.models import Plan


# Requirement, PlanRequirement
class Requirement(models.Model):
    # 공통
    NONE = 'none'  # 구분 없음

    # Requirement Type
    MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
    MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
    GENERAL = 'general'  # 일반 선택
    GENERAL_ELECTIVE = 'general_elective'  # 교양
    TEACHING = 'teaching'  # 교직
    ALL = 'all'  # 전체

    # Requirement Type Detail
    BASE_OF_STUDY = 'base_of_study'  # 학문의 기초
    WORLD_OF_STUDY = 'world_of_study'  # 학문의 세계
    OTHER = 'other'  # 일반 교양

    # Requirement Type Detail Detail
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

    REQUIREMENT_TYPE = (
        (NONE, 'none'),
        (MAJOR_REQUIREMENT, 'major_requirement'),
        (MAJOR_ELECTIVE, 'major_elective'),
        (GENERAL, 'general'),
        (GENERAL_ELECTIVE, 'general_elective'),
        (TEACHING, 'teaching'),
        (ALL, 'all'),
    )
    REQUIREMENT_TYPE_DETAIL = (
        (NONE, 'none'),
        (BASE_OF_STUDY, 'base_of_study'),
        (WORLD_OF_STUDY, 'world_of_study'),
        (OTHER, 'other'),
    )
    REQUIREMENT_TYPE_DETAIL_DETAIL = (
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
    major = models.ForeignKey(Major, related_name='requirement', on_delete=models.CASCADE)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=500, blank=True)
    is_credit_requirement = models.BooleanField()
    required_credit = models.PositiveSmallIntegerField(default=0)
    requirement_type = models.CharField(choices=REQUIREMENT_TYPE)
    requirement_type_detail = models.CharField(choices=REQUIREMENT_TYPE_DETAIL, default=NONE)
    requirement_type_detail_detail = models.CharField(choices=REQUIREMENT_TYPE_DETAIL_DETAIL, default=NONE)

    class Meta:
        ordering = ['-end_year', '-start_year']  # 최신순


class PlanRequirement(models.Model):
    plan = models.ForeignKey(Plan, related_name='planrequirement', on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, related_name='planrequirement', on_delete=models.CASCADE)
    is_fulfilled = models.BooleanField(default=False)
    earned_credit = models.PositiveSmallIntegerField(default=0)
