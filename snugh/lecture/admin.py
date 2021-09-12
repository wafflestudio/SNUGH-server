from django.contrib import admin
from lecture.models import Lecture, Plan, Semester, PlanMajor, SemesterLecture, MajorLecture


admin.site.register(Lecture)
admin.site.register(Plan)
admin.site.register(Semester)
admin.site.register(PlanMajor)
admin.site.register(SemesterLecture)
admin.site.register(MajorLecture)
