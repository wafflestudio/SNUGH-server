"""Utils related to Semester APIs."""

from core.lecture.models import SemesterLecture
from core.lecture.const import *
from core.semester.models import Semester


def add_semester_credits(semesterlecture: SemesterLecture, semester: Semester) -> Semester:
    """Add semesterLecture's credits to semester credits."""
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
    """Subtract semesterLecture's credits to semester credits."""
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