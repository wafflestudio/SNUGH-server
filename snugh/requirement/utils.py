from typing import Union
from requirement.models import *

def calculate_progress(std: int, value: int) -> Union[int, float]:
    """Calculate ratio of current progress."""
    if std == 0:
        return 1
    else:
        return 1 if round(value / std, 2) > 1 else round(value / std, 2)

def requirement_histroy_generator(
    requirement: Requirement, 
    entrance_year: int,
    past_required_credit: int,
    curr_required_credit: int
    ):
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
    return req_history
