from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('jobs/', views.JobListCreateView.as_view(), name='jobs-list-create'),
    path('jobs/search/', views.JobSearchView.as_view(), name='jobs-search'),
    path('resumes/', views.ResumeUploadView.as_view(), name='resumes-upload'),
    path('applications/', views.ApplicationListView.as_view(), name='applications-list'),
    path('applications/create/', views.ApplicationCreateView.as_view(), name='applications-create'),
    path('applications/<int:pk>/status/', views.update_application_status, name='application-update-status'),
    path('reports/stats/', views.reporting_stats, name='reporting-stats'),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('register/employer/', views.EmployerRegisterView.as_view(), name='register-employer'),
    path('register/candidate/', views.CandidateRegisterView.as_view(), name='register-candidate'),
    # reporting per-employer and per-job
    path('reports/employer/<int:pk>/', views.EmployerReportView.as_view(), name='report-employer'),
    path('reports/job/<int:pk>/', views.JobReportView.as_view(), name='report-job'),
    # admin user management
    path('admin/users/', views.UserListAdminView.as_view(), name='admin-users-list'),
    path('admin/users/<int:pk>/', views.UserDetailAdminView.as_view(), name='admin-users-detail'),
]
