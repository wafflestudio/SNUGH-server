from typing import Union

def calculate_progress(std: int, value: int) -> Union[int, float]:
    if std == 0:
        return 1
    else:
        return 1 if round(value / std, 2) > 1 else round(value / std, 2)
