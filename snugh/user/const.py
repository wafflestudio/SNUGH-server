"""Constants related to Major, User."""

from core.const import *

# UserProfile
ACTIVE = 'active'
INACTIVE = 'inactive'
BREAK = 'break'

STUDENT_STATUS = (
    (ACTIVE, 'active'),  # 재학
    (INACTIVE, 'inactive'),  # 서비스 탈퇴
    (BREAK, 'break'),  # 휴학
)
