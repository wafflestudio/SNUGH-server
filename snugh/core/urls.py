from django.urls import include, path
from rest_framework.routers import SimpleRouter
from core.plan.views import PlanViewSet 
from core.lecture.views import LectureViewSet 
from core.requirement.views import RequirementViewSet
from core.semester.views import SemesterViewSet
from core.major.views import MajorViewSet

app_name = 'core'

router = SimpleRouter() 
router.register('plan', PlanViewSet, basename='plan')
router.register('requirement', RequirementViewSet, basename='requirement')
router.register('lecture', LectureViewSet, basename='lecture')
router.register('semester', SemesterViewSet, basename='semester')
router.register('major', MajorViewSet, basename='major')  

urlpatterns = [
    path('', include((router.urls))),
]
