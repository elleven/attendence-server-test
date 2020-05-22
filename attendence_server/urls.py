"""attendence_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from attendence import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.HomePageView.as_view(), name='home'),
    url(r'^login', views.LoginView.as_view(), name='login'),
    url(r'^logout', views.LogoutView.as_view(), name='logout'),
    url(r'^attendence/query', views.PersonQueryView.as_view(), name='person_query'),
    url(r'^approval/query', views.ApprovalQueryView.as_view(), name='approval_query'),
    url(r'^attendence/dept/query', views.DeptQueryView.as_view(), name='dept_attendence_query'),
    url(r'^dept$', views.Org, name='org'),
    url(r'^dept/info', views.DeptDetailView.as_view(), name='dept_detail'),
    url(r'^user/info/(?P<jobnumber>\d+)$', views.UserQuery.as_view(), name='user_info'),
    url(r'^attendence/stats', views.PersonAttendanceStats.as_view(), name='attendence_stats'),
    url(r'^approval/stats', views.ApprovalStatsView.as_view(), name='approval_stats'),
    url(r'^unclock/query', views.UclockReportView.as_view(), name='unclock_query'),
    url(r'^attendence/current', views.CurrentAttendenceView.as_view(), name='current_attendence'),
    url(r'^newuser/manager', views.NewUserlistView.as_view(), name='newuser_manager'),
    url(r'^newuser/edit', views.NewUserView.as_view(), name='newuser_edit'),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('attendence.urls')),

]
