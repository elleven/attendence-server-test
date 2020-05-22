from django.conf.urls import url, include
from . import views
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'department', views.DepartmentViewSet)
router.register(r'user', views.UserView)
router.register(r'approval', views.ApprovalRecordView)
router.register(r'attendance', views.AttendanceRecordView)

urlpatterns = [
    url(r'', include(router.urls)),
]