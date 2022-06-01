"""Utils related to Requirement APIs."""

from typing import Union
from core.requirement.models import *


def calculate_progress(std: int, value: int) -> Union[int, float]:
    """Calculate ratio of current progress."""
    if std == 0:
        return 1
    else:
        return 1 if round(value / std, 2) > 1 else round(value / std, 2)
