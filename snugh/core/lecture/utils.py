"""Utils related to Lecture APIs."""

from core.lecture.models import SemesterLecture
from core.lecture.const import *
from core.plan.models import Plan
from core.major.models import Major
from django.contrib.auth import get_user_model
from core.major.const import *
from django.db.models import Case, When, Value, IntegerField
from snugh.exceptions import NotOwner, NotFound
from core.semester.models import Semester
from core.semester.utils import add_semester_credits, sub_semester_credits

User = get_user_model()

def update_lecture_info(
    user: User, 
    plan_id: int, 
    semesterlectures: SemesterLecture = None, 
    semester: Semester = None) -> Plan:
    """Update lecture info."""
    try:
        plan = Plan.objects.prefetch_related(
                'user',
                'user__userprofile',
                'semester', 
                'planmajor',
                'semester__semesterlecture',
                'semester__semesterlecture__lecture',
                'semester__semesterlecture__lecture__majorlecture',
                'semester__semesterlecture__lecture__lecturecredit'
                ).get(id=plan_id)
    except Plan.DoesNotExist:
        raise NotFound()
    owner = plan.user
    if user != owner:
        raise NotOwner()
    planmajors = plan.planmajor.all()
    majors = Major.objects.filter(planmajor__in=planmajors)\
        .annotate(custom_order=Case(When(major_type=SINGLE_MAJOR, then=Value(0)),
                                    When(major_type=MAJOR, then=Value(1)),
                                    When(major_type=GRADUATE_MAJOR, then=Value(2)),
                                    When(major_type=INTERDISCIPLINARY_MAJOR, then=Value(3)),
                                    When(major_type=INTERDISCIPLINARY_MAJOR_FOR_TEACHER, then=Value(4)),
                                    When(major_type=DOUBLE_MAJOR, then=Value(5)),
                                    When(major_type=INTERDISCIPLINARY, then=Value(6)),
                                    When(major_type=MINOR, then=Value(7)),
                                    When(major_type=INTERDISCIPLINARY_PROGRAM, then=Value(8)),
                                    default=Value(9),
                                    output_field=IntegerField(), ))\
        .order_by('custom_order')
    none_major = Major.objects.get(id=DEFAULT_MAJOR_ID)
    updated_semesters = []
    if semesterlectures and semester:
        updated_semester = __update_lecture_info(user, majors, semesterlectures, semester, none_major)
        updated_semesters.append(updated_semester)
    else:
        semesters = plan.semester.all()
        for semester in semesters:
            semesterlectures = semester.semesterlecture.all()
            updated_semester = __update_lecture_info(user, majors, semesterlectures, semester, none_major)
            updated_semesters.append(updated_semester)
    Semester.objects.bulk_update(
        updated_semesters, 
        ['major_requirement_credit', 
        'major_elective_credit', 
        'general_credit', 
        'general_elective_credit'])
    return plan


def __update_lecture_info(
    user:User, 
    majors: Major, 
    semesterlectures: SemesterLecture, 
    semester: Semester,
    none_major: Major) -> Semester:
    """Private method using in updating lecture info."""
    updated_semesterlectures = []
    std1 = user.userprofile.entrance_year
    std2 = semester.year
    for semesterlecture in semesterlectures:
        tmp_majors = majors

        if not semesterlecture.is_modified:
            semester = sub_semester_credits(semesterlecture, semester)
            lecture = semesterlecture.lecture
            if semesterlecture.lecture_type != GENERAL:
                major_count = 0
                majorlectures = lecture.majorlecture.all()
                for major in tmp_majors:
                    if major_count > 1:
                        break
                    candidate_majorlectures = majorlectures.filter(
                        major=major,
                        start_year__lte=std1,
                        end_year__gte=std1)\
                    .exclude(lecture_type__in=[GENERAL, GENERAL_ELECTIVE])\
                    .order_by('-lecture_type')
                    if candidate_majorlectures.exists():
                        candidate_majorlecture = candidate_majorlectures[0]
                        if major_count == 0:
                            semesterlecture.lecture_type = candidate_majorlecture.lecture_type
                            semesterlecture.lecture_type1 = candidate_majorlecture.lecture_type
                            semesterlecture.recognized_major1 = major
                        elif major_count == 1:
                            semesterlecture.lecture_type2 = candidate_majorlecture.lecture_type
                            semesterlecture.recognized_major2 = major
                        major_count += 1

                if major_count != 2:
                    if major_count == 1:
                        tmp_majors = tmp_majors.exclude(id=semesterlecture.recognized_major1.id)
                    for major in tmp_majors:
                        if major_count > 1:
                            break

                        candidate_majorlectures = lecture.majorlecture.filter(
                            major=major,
                            start_year__lte=std2,
                            end_year__gte=std2)\
                        .exclude(lecture_type__in=[GENERAL, GENERAL_ELECTIVE])\
                        .order_by('-lecture_type')
                        if candidate_majorlectures.exists() != 0:
                            candidate_majorlecture = candidate_majorlectures[0]
                            if major_count == 0:
                                semesterlecture.lecture_type = candidate_majorlecture.lecture_type
                                semesterlecture.lecture_type1 = candidate_majorlecture.lecture_type
                                semesterlecture.recognized_major1 = major
                            elif major_count == 1:
                                semesterlecture.lecture_type2 = candidate_majorlecture.lecture_type
                                semesterlecture.recognized_major2 = major
                            major_count += 1

                if major_count == 1:
                    semesterlecture.lecture_type2 = NONE
                    semesterlecture.recognized_major2 = none_major
                elif major_count == 0:
                    semesterlecture.lecture_type = GENERAL_ELECTIVE
                    semesterlecture.lecture_type1 = GENERAL_ELECTIVE
                    semesterlecture.recognized_major1 = none_major
                    semesterlecture.lecture_type2 = NONE
                    semesterlecture.recognized_major2 = none_major

            lecturecredits = lecture.lecturecredit.filter(start_year__lte=std2,
                                                            end_year__gte=std2)

            if lecturecredits.exists():
                semesterlecture.credit = lecturecredits[0].credit
            semester = add_semester_credits(semesterlecture, semester)
            updated_semesterlectures.append(semesterlecture)
    SemesterLecture.objects.bulk_update(
        updated_semesterlectures, 
        ['lecture_type',
        'lecture_type1',
        'lecture_type2',
        'recognized_major1',
        'recognized_major2'])
    return semester
