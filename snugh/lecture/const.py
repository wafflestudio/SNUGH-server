# 구분 없음
NONE = 'none'
DEFAULT_MAJOR_ID = 1

# Semester Type
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

# Lecture Type
MAJOR_REQUIREMENT = 'major_requirement'  # 전공 필수
MAJOR_ELECTIVE = 'major_elective'  # 전공 선택
GENERAL = 'general'  # 교양
GENERAL_ELECTIVE = 'general_elective'  # 일반 선택
TEACHING = 'teaching'  # 교직

LECTURE_TYPE = (
    (MAJOR_REQUIREMENT, 'major_requirement'),
    (MAJOR_ELECTIVE, 'major_elective'),
    (GENERAL, 'general'),
    (GENERAL_ELECTIVE, 'general_elective'),
    (TEACHING, 'teaching'),
)