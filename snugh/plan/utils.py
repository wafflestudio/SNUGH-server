"""Utils related to Plan APIs."""

from plan.models import Plan, PlanMajor
from user.models import Major
from requirement.models import PlanRequirement
from snugh.exceptions import DuplicationError, FieldError, NotFound
from django.db.utils import IntegrityError


def plan_major_requirement_generator(plan: Plan, majors: dict, entrance_year: int) -> bool:
    """Generate PlanMajor & PlanRequirement."""
    planmajors = []
    planrequirements = []
    try:
        for major in majors:
            major_name = major.get('major_name')
            major_type = major.get('major_type')
            if not (major_name and major_type):
                raise FieldError("Field missing [major_name, major_type]")
            major = Major.objects.get(major_name=major_name, major_type=major_type)
            planmajors.append(PlanMajor(plan=plan, major=major))
            requirements = major.requirement.filter(start_year__lte=entrance_year, end_year__gte=entrance_year)
            for requirement in requirements:
                planrequirements.append(PlanRequirement(plan=plan, 
                                                        requirement=requirement, 
                                                        required_credit=requirement.required_credit))
        
        PlanMajor.objects.bulk_create(planmajors)
        PlanRequirement.objects.bulk_create(planrequirements)
    except Major.DoesNotExist:
        raise NotFound("Does not exist [Major]")
    except IntegrityError:
        raise DuplicationError("Already exists [PlanMajor]")

    return True
    