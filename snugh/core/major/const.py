from core.const import *

# Major
MAJOR = 'major'
DOUBLE_MAJOR = 'double_major'
MINOR = 'minor'
INTERDISCIPLINARY_MAJOR = 'interdisciplinary_major'
INTERDISCIPLINARY = 'interdisciplinary'
SINGLE_MAJOR = 'single_major'
INTERDISCIPLINARY_MAJOR_FOR_TEACHER = 'interdisciplinary_major_for_teacher'
STUDENT_DIRECTED_MAJOR = 'student_directed_major'
INTERDISCIPLINARY_PROGRAM = 'interdisciplinary_program'
GRADUATE_MAJOR = 'graduate_major'

MAJOR_TYPE = (
    (MAJOR, 'major'),
    (DOUBLE_MAJOR, 'double_major'),  # 복수전공
    (MINOR, 'minor'),  # 부전공
    (INTERDISCIPLINARY_MAJOR, 'interdisciplinary_major'),  # 연합전공
    (INTERDISCIPLINARY, 'interdisciplinary'),  # 연계전공
    (SINGLE_MAJOR, 'single_major'),  # 단일전공
    (INTERDISCIPLINARY_MAJOR_FOR_TEACHER, 'interdisciplinary_major_for_teacher'),  # 교직연합전공
    (STUDENT_DIRECTED_MAJOR, 'student_directed_major'),  # 학생설계전공
    (INTERDISCIPLINARY_PROGRAM, 'interdisciplinary_program'),  # 협동과정
    (GRADUATE_MAJOR, 'graduate_major'),  # 대학원
)

DEFAULT_MAJOR_ID = 1

DEFAULT_MAJOR_NAME = 'none'
DEFAULT_MAJOR_TYPE = 'major'