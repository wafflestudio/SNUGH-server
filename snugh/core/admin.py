from django.contrib import admin
from core.plan.models import Plan, PlanMajor
from core.lecture.models import Lecture, SemesterLecture, MajorLecture
from core.requirement.models import Requirement, PlanRequirement
from core.semester.models import Semester
from core.major.models import Major, UserMajor

admin.site.register(Plan)
admin.site.register(PlanMajor)
admin.site.register(Lecture)
admin.site.register(SemesterLecture)
admin.site.register(MajorLecture)
admin.site.register(Requirement)
admin.site.register(PlanRequirement)
admin.site.register(Semester)
admin.site.register(Major)
admin.site.register(UserMajor)
