from django.urls import include, path 
from rest_framework.routers import SimpleRouter
from lecture.views import PlanViewSet, SemesterViewSet, LectureViewSet 


app_name = 'lecture'

router = SimpleRouter() 
router.register('plan', PlanViewSet, basename='plan')
router.register('semester', SemesterViewSet, basename='semester')
router.register('lecture', LectureViewSet, basename='lecture')

urlpatterns = [
    path('', include((router.urls))),
]

"""
from django.conf import settings

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
"""