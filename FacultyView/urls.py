from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='faculty_login'),
    path('logout/', views.logout_view, name='faculty_logout'),
    path('dashboard/', views.dashboard, name='faculty_dashboard'),
    path('add-student/', views.add_student, name='add_student'),
    path('add-course/', views.add_course, name='add_course'),
    path('create-attendance/', views.mark_attendance, name='create_attendance'),
    path('attendance-session/<uuid:session_id>/', views.view_attendance_session, name='view_attendance_session'),
    path('attendance-history/', views.attendance_history, name='attendance_history'),
    path('view-all-students/', views.view_all_students, name='view_all_students'),
    path('remove-student/<int:student_id>/', views.remove_student, name='remove_student'),
    path('attendance-sessions/', views.list_attendance_sessions, name='list_attendance_sessions'),
    path('end-attendance-session/<uuid:session_id>/', views.end_attendance_session, name='end_attendance_session'),
]
