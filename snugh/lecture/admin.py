from django.contrib import admin
from lecture.models import Lecture, SemesterLecture, MajorLecture


admin.site.register(Lecture)
admin.site.register(SemesterLecture)
admin.site.register(MajorLecture)
