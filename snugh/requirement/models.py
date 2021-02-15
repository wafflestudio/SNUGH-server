from django.db import models
from django.contrib.auth.models import User
from user.models import Major
from lecture.models import Plan

# Requirement, PlanRequirement

class Requirement(models.Model):
    REQUIREMENT_TYPE = (
        (1, 'general'),  # 교양
        (2, 'major_requirement'),  # 전공 필수
        (3, 'major_elective'),  # 전공 선택
        (4, 'all'), # 전체 
        (5, 'none'), # 해당없음(일반규정)
    )
    REQUIREMENT_TYPE_DETAIL = (
        (1, 'none'),  # 구분 없음
        (2, 'base_of_study'),  # 학문의 기초
        (3, 'world_of_study'),  # 학문의 세계
        (4, 'other'),  # 일반교양
    )
    REQUIREMENT_TYPE_DETAIL_DETAIL = (
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
    major =  models.ForeignKey(Major, related_name='requirement', on_delete=models.CASCADE)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=500, blank=True)
    is_credit_requirement = models.BooleanField()
    required_credit = models.PositiveSmallIntegerField(default=0)
    requirement_type = models.PositiveSmallIntegerField(choices=REQUIREMENT_TYPE)
    lecture_type_detail = models.PositiveSmallIntegerField(choices=REQUIREMENT_TYPE_DETAIL, default=1)
    lecture_type_detail_detail = models.PositiveSmallIntegerField(choices=REQUIREMENT_TYPE_DETAIL_DETAIL, default=1)

    class Meta:
        ordering = ['-end_year', '-start_year'] # 최신순

class PlanRequirement(models.Model):
    plan =  models.ForeignKey(Plan, related_name='planrequirement', on_delete=models.CASCADE)
    requirement = models.ForeignKey(Requirement, related_name='planrequirement', on_delete=models.CASCADE)
    is_fulfilled = models.BooleanField(default=False)
    earned_credit = models.PositiveSmallIntegerField(default=0)