from lecture.models import Semester, SemesterLecture, Plan
from lecture.models import LectureTypeChangeHistory, CreditChangeHistory
from user.models import Major, User
from lecture.const import *
from django.db.models import Case, When, Value, IntegerField
from snugh.exceptions import NotOwner, NotFound
from typing import List

# Common Functions
def add_credits(semesterlecture):
    semester = semesterlecture.semester
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit
    return semester


def subtract_credits(semesterlecture):
    semester = semesterlecture.semester
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit -= semesterlecture.credit
    return semester


def add_semester_credits(semesterlecture: SemesterLecture, semester: Semester) -> Semester:
    """ Add SemesterLecture's credits to Semester credits. """
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit
    return semester

def sub_semester_credits(semesterlecture: SemesterLecture, semester: Semester) -> Semester:
    """ Subtract SemesterLecture's credits to Semester credits. """
    if semesterlecture.lecture_type == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type2 == MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == MAJOR_ELECTIVE or semesterlecture.lecture_type == TEACHING:
        semester.major_elective_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL:
        semester.general_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == GENERAL_ELECTIVE:
        semester.general_elective_credit -= semesterlecture.credit
    return semester

def update_lecture_info(\
    user: User, 
    plan_id: int, 
    semesterlectures: SemesterLecture = None, 
    semester: Semester = None) -> Plan:
    """ Update lecture info """
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
    none_major: Major = Major.objects.get(id=DEFAULT_MAJOR_ID)) -> Semester:

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

def lecturetype_history_generator(
    user: User, 
    semesterlecture: SemesterLecture, 
    lecture_type: str,
    curr_recognized_majors: List[Major] = [],
    curr_lecture_types: List[str] = []
    ) -> bool:
    """ Generate LectureType Change History """
    none_major = Major.objects.get(id=DEFAULT_MAJOR_ID)
    user_entrance = user.userprofile.entrance_year
    lecture = semesterlecture.lecture
    histories = []
    if lecture_type in [GENERAL, GENERAL_ELECTIVE]:
        recognized_majors = [none_major, semesterlecture.recognized_major1, semesterlecture.recognized_major2]
        past_lecture_types = [NONE, semesterlecture.lecture_type1, semesterlecture.lecture_type2]
        curr_lecture_types = [lecture_type, NONE, NONE]

        # lecturetypechangehistory의 major가 default major 인 유일한 경우 --??
        for i in range(3):
            recognized_major = recognized_majors[i]
            past_lecture_type = past_lecture_types[i]
            curr_lecture_type = curr_lecture_types[i]

            if i==0 or recognized_major != none_major:
                lecturetypechangehistory, _ = LectureTypeChangeHistory.objects.get_or_create(
                    major=recognized_major,
                    lecture=lecture,
                    entrance_year=user_entrance,
                    past_lecture_type=past_lecture_type,
                    curr_lecture_type=curr_lecture_type)
                lecturetypechangehistory.change_count += 1
                histories.append(lecturetypechangehistory)

    elif lecture_type in [MAJOR_ELECTIVE, MAJOR_REQUIREMENT]:

        past_recognized_major_check = [False, False]
        curr_recognized_major_check = [False, False]
        past_recognized_majors = [semesterlecture.recognized_major1, semesterlecture.recognized_major2]
        past_lecture_types = [semesterlecture.lecture_type1, semesterlecture.lecture_type2]

        for i, past_recognized_major in enumerate(past_recognized_majors):
            for j, curr_recognized_major in enumerate(curr_recognized_majors):
                if curr_recognized_major_check[j] == False:
                    if past_recognized_major == curr_recognized_major:
                        curr_recognized_major_check[j] = True
                        past_recognized_major_check[i] = True
                        if past_lecture_types[i] != curr_lecture_types[j] and past_recognized_major != none_major:
                            lecturetypechangehistory, _ = LectureTypeChangeHistory.objects.get_or_create(
                                major=past_recognized_major,
                                lecture=lecture,
                                entrance_year=user_entrance,
                                past_lecture_type=past_lecture_types[i],
                                curr_lecture_type=curr_lecture_types[j])
                            lecturetypechangehistory.change_count += 1
                            histories.append(lecturetypechangehistory)

            if not (past_recognized_major_check[i] or past_lecture_types[i] in [NONE, GENERAL_ELECTIVE]):
                lecturetypechangehistory, _ = LectureTypeChangeHistory.objects.get_or_create(
                    major=past_recognized_major,
                    lecture=lecture,
                    entrance_year=user_entrance,
                    past_lecture_type=past_lecture_types[i],
                    curr_lecture_type=NONE)
                lecturetypechangehistory.change_count += 1
                histories.append(lecturetypechangehistory)

        for i, curr_recognized_major in enumerate(curr_recognized_majors):
            if not (curr_recognized_major_check[i] or curr_lecture_types[i] in [NONE, GENERAL_ELECTIVE]):
                lecturetypechangehistory, _ = LectureTypeChangeHistory.objects.get_or_create(
                    major=curr_recognized_major,
                    lecture=lecture,
                    entrance_year=user_entrance,
                    past_lecture_type=NONE,
                    curr_lecture_type=curr_lecture_types[i])
                lecturetypechangehistory.change_count += 1
                histories.append(lecturetypechangehistory)
                
    LectureTypeChangeHistory.objects.bulk_update(histories, fields=['change_count'])
    return True

def credit_history_generator(user: User, semesterlecture: SemesterLecture, credit: int) -> bool:
    """Create semester lecture credit change histroy"""
    none_major = Major.objects.get(id=DEFAULT_MAJOR_ID)
    user_entrance = user.userprofile.entrance_year
    recognized_majors = list(set([semesterlecture.recognized_major1, semesterlecture.recognized_major2]))
    year_taken = semesterlecture.semester.year
    if len(recognized_majors) > 1:
        recognized_majors = [rm for rm in recognized_majors if rm != none_major]
    histories = []
    for recognized_major in recognized_majors:
        creditchangehistory, _ = CreditChangeHistory.objects.get_or_create(
            major=recognized_major,
            lecture=semesterlecture.lecture,
            entrance_year=user_entrance,
            year_taken=year_taken,
            past_credit=semesterlecture.credit,
            curr_credit=credit)
        creditchangehistory.change_count += 1
        histories.append(creditchangehistory)
    CreditChangeHistory.objects.bulk_update(histories, fields=['change_count'])
    return True
