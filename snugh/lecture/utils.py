from factory.django import DjangoModelFactory
from .models import Plan, Semester, Lecture, Semester, SemesterLecture, Major


# Common Functions
def add_credits(semesterlecture):
    semester = semesterlecture.semester
    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit
    return semester


def subtract_credits(semesterlecture):
    semester = semesterlecture.semester
    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit -= semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit -= semesterlecture.credit
    return semester


def add_semester_credits(semesterlecture: SemesterLecture, semester: Semester) -> Semester:
    """ Add SemesterLecture's credits to Semester credits. """
    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit
    return semester


def sub_semester_credits(semesterlecture, semester):
    """ Subtract SemesterLecture's credits to Semester credits. """
    if semesterlecture.lecture_type == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type2 == SemesterLecture.MAJOR_REQUIREMENT:
        semester.major_requirement_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.MAJOR_ELECTIVE or semesterlecture.lecture_type == SemesterLecture.TEACHING:
        semester.major_elective_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL:
        semester.general_credit += semesterlecture.credit
    elif semesterlecture.lecture_type == SemesterLecture.GENERAL_ELECTIVE:
        semester.general_elective_credit += semesterlecture.credit
    return semester
