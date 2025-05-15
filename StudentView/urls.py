from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.student_login, name='student_login'),
    path('logout/', views.student_logout, name='student_logout'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('mark-attendance/<str:session_code>/', views.mark_attendance, name='mark_attendance'),
    path('course-attendance/<int:course_id>/', views.get_course_attendance, name='course_attendance'),
    path('attendance-report/', views.student_attendance_report, name='student_attendance_report'),
]
