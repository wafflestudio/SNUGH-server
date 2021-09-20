from django.urls import include, path 
from rest_framework.routers import SimpleRouter
from bug_report.views import BugReportViewSet


app_name = 'bug'

router = SimpleRouter() 
router.register('bug', BugReportViewSet, basename='bug')

urlpatterns = [
    path('', include((router.urls))),
]
