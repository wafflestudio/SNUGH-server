from django.urls import include, path 
from rest_framework.routers import SimpleRouter
from lecture.views import LectureViewSet 

app_name = 'lecture'

router = SimpleRouter() 
router.register('lecture', LectureViewSet, basename='lecture')

urlpatterns = [
    path('', include((router.urls))),
]
