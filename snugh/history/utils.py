
from user.models import User, Major
from requirement.models import Requirement
from lecture.models import SemesterLecture
from history.models import LectureTypeChangeHistory, CreditChangeHistory, RequirementChangeHistory
from lecture.const import *
from datetime import date
from typing import List


def lecturetype_history_generator(
    user: User, 
    semesterlecture: SemesterLecture, 
    lecture_type: str,
    curr_recognized_majors: List[Major] = [],
    curr_lecture_types: List[str] = []
    ) -> bool:
    """Generate lecture type change history."""
    none_major = Major.objects.get(id=DEFAULT_MAJOR_ID)
    user_entrance = user.userprofile.entrance_year
    lecture = semesterlecture.lecture
    histories = []
    if lecture_type in [GENERAL, GENERAL_ELECTIVE]:
        recognized_majors = [none_major, semesterlecture.recognized_major1, semesterlecture.recognized_major2]
        past_lecture_types = [NONE, semesterlecture.lecture_type1, semesterlecture.lecture_type2]
        curr_lecture_types = [lecture_type, NONE, NONE]

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
                lecturetypechangehistory.updated_at = date.today()
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
                            lecturetypechangehistory.updated_at = date.today()
                            histories.append(lecturetypechangehistory)

            if not (past_recognized_major_check[i] or past_lecture_types[i] in [NONE, GENERAL_ELECTIVE]):
                lecturetypechangehistory, _ = LectureTypeChangeHistory.objects.get_or_create(
                    major=past_recognized_major,
                    lecture=lecture,
                    entrance_year=user_entrance,
                    past_lecture_type=past_lecture_types[i],
                    curr_lecture_type=NONE)
                lecturetypechangehistory.change_count += 1
                lecturetypechangehistory.updated_at = date.today()
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
                lecturetypechangehistory.updated_at = date.today()
                histories.append(lecturetypechangehistory)
                
    LectureTypeChangeHistory.objects.bulk_update(histories, fields=['change_count', 'updated_at'])
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
        creditchangehistory.updated_at = date.today()
        histories.append(creditchangehistory)
    CreditChangeHistory.objects.bulk_update(histories, fields=['change_count', 'updated_at'])
    return True


def requirement_histroy_generator(
    requirement: Requirement, 
    entrance_year: int,
    past_required_credit: int,
    curr_required_credit: int
    ) -> RequirementChangeHistory:
    """
    Create requirement change histroy.
    Need to save returned requirement histroy. 
    """
    req_history, _ = RequirementChangeHistory.objects.get_or_create(
        requirement=requirement,
        entrance_year=entrance_year,
        past_required_credit=past_required_credit,
        curr_required_credit=curr_required_credit
        )
    req_history.change_count += 1
    req_history.updated_at = date.today()
    return req_history
