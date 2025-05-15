from django.shortcuts import render, redirect, get_object_or_404
from FacultyView.models import Student, Attendance, Course, AttendanceSession
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login, logout
from .forms import StudentLoginForm
from django.utils import timezone
import qrcode
import socket
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

# Create your views here.

present = set()


def add_manually_post(request):
    student_roll = request.POST["student-name"]
    student = Student.objects.get(s_roll=student_roll)
    present.add(student)
    return HttpResponseRedirect("/submitted")


def submitted(request):
    return render(request, "StudentView/Submitted.html")

def student_login(request):
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            request.session['student_id'] = student.id
            messages.success(request, 'Successfully logged in.')
            return redirect('student_dashboard')
    else:
        form = StudentLoginForm()
    return render(request, 'StudentView/login.html', {'form': form})

def student_logout(request):
    request.session.flush()
    messages.success(request, 'Successfully logged out.')
    return redirect('student_login')

def get_course_attendance(request, course_id):
    student_id = request.session.get('student_id')
    if not student_id:
        messages.warning(request, 'Please log in to access the dashboard.')
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=student_id)
        course = Course.objects.get(id=course_id)
        
        # Get all attendance records for this course
        attendance_records = Attendance.objects.filter(
            student=student,
            course=course
        ).select_related('session').order_by('-date', '-created_at')
        
        return JsonResponse({
            'course_code': course.code,
            'course_name': course.name,
            'attendance_records': [
                {
                    'date': record.date.strftime('%B %d, %Y'),
                    'time': record.session.start_time.strftime('%I:%M %p') if record.session else 'N/A',
                    'status': record.status,
                    'session_id': record.session.session_code if record.session else 'N/A'
                }
                for record in attendance_records
            ]
        })
    except (Student.DoesNotExist, Course.DoesNotExist):
        return JsonResponse({'error': 'Student or course not found'}, status=404)

def student_dashboard(request):
    student_id = request.session.get('student_id')
    if not student_id:
        messages.warning(request, 'Please log in to access the dashboard.')
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=student_id)
        print(f"Found student: {student.name} (ID: {student.id})")
        
        # Get all courses where the student has attendance records
        enrolled_courses = Course.objects.filter(
            attendance__student=student
        ).distinct().select_related('faculty')
        
        print(f"Found {enrolled_courses.count()} enrolled courses")
        for course in enrolled_courses:
            print(f"Course: {course.name} (ID: {course.id})")
        
        # Get active attendance sessions for these courses
        active_sessions = AttendanceSession.objects.filter(
            course__in=enrolled_courses,
            is_active=True,
            date__gte=timezone.now().date()
        ).select_related('course').order_by('date', 'start_time')
        
        print(f"Found {active_sessions.count()} active sessions")
        
        # Get attendance records for this student from actual sessions only
        attendance_records = Attendance.objects.filter(
            student=student,
            session__isnull=False  # Only show records from actual sessions
        ).select_related('course', 'session').order_by('-date', '-created_at')
        
        print(f"Found {attendance_records.count()} attendance records")
        
        context = {
            'student': student,
            'enrolled_courses': enrolled_courses,
            'active_sessions': active_sessions,
            'attendance_records': attendance_records,
        }
        return render(request, 'StudentView/dashboard.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('student_login')

def mark_attendance(request, session_code):
    if 'student_id' not in request.session:
        messages.error(request, 'Please log in to mark attendance.')
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=request.session['student_id'])
        session = get_object_or_404(AttendanceSession, session_code=session_code, is_active=True)
        
        # Check if attendance already exists
        existing_attendance = Attendance.objects.filter(
            student=student,
            session=session
        ).first()
        
        if existing_attendance:
            messages.warning(request, 'You have already marked attendance for this session.')
            return redirect('student_dashboard')
        
        # Get current time in the local timezone
        now = timezone.localtime(timezone.now())
        
        # Convert session times to datetime for comparison
        session_date = session.date
        start_datetime = timezone.make_aware(
            datetime.combine(session_date, session.start_time),
            timezone=timezone.get_current_timezone()
        )
        grace_end_datetime = start_datetime + timedelta(minutes=session.grace_period)
        
        print(f"Current time: {now}")
        print(f"Start time: {start_datetime}")
        print(f"Grace end time: {grace_end_datetime}")
        print(f"Grace period: {session.grace_period} minutes")
        
        # Determine attendance status based on scanning time
        if now <= start_datetime:
            # Student scanned before or at start time
            status = 'present'
            message = 'Attendance marked as Present (on time)'
            print("Status: Present (on time)")
        elif now <= grace_end_datetime:
            # Student scanned after start time but within grace period
            status = 'late'
            message = 'Attendance marked as Late (within grace period)'
            print("Status: Late (within grace period)")
        else:
            # Student scanned after grace period
            status = 'absent'
            message = 'Attendance marked as Absent (beyond grace period)'
            print("Status: Absent (beyond grace period)")
        
        # Create attendance record
        attendance = Attendance.objects.create(
            student=student,
            course=session.course,
            session=session,
            date=session.date,
            status=status
        )
        
        messages.success(request, message)
        return redirect('student_dashboard')
        
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('student_login')
    except Exception as e:
        messages.error(request, f'Error marking attendance: {str(e)}')
        return redirect('student_dashboard')

def student_attendance_report(request):
    student_id = request.session.get('student_id')
    if not student_id:
        messages.warning(request, 'Please log in to access the attendance report.')
        return redirect('student_login')
    
    try:
        student = Student.objects.get(id=student_id)
        
        # Get all attendance records for this student
        attendance_records = Attendance.objects.filter(
            student=student,
            session__isnull=False  # Only include records from actual sessions
        ).select_related('course', 'session')
        
        # Calculate attendance statistics
        total_classes = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        late_count = attendance_records.filter(status='late').count()
        absent_count = attendance_records.filter(status='absent').count()
        
        # Calculate attendance percentage (present + late count as attendance)
        attendance_percentage = ((present_count + late_count) / total_classes * 100) if total_classes > 0 else 0
        
        # Determine attendance status
        if attendance_percentage >= 90:
            status = 'Elite'
            status_class = 'success'
        elif attendance_percentage >= 60:
            status = 'Good'
            status_class = 'info'
        else:
            status = 'Bad'
            status_class = 'danger'
        
        # Get course-wise statistics
        course_stats = {}
        for record in attendance_records:
            course = record.course
            if course not in course_stats:
                course_stats[course] = {
                    'total': 0,
                    'present': 0,
                    'late': 0,
                    'absent': 0,
                    'present_percentage': 0,
                    'late_percentage': 0,
                    'absent_percentage': 0,
                    'attendance_percentage': 0
                }
            
            course_stats[course]['total'] += 1
            # Safely increment the status count
            record_status = getattr(record, 'status', 'absent')  # Default to 'absent' if status is not set
            if record_status in ['present', 'late', 'absent']:
                course_stats[course][record_status] += 1
        
        # Calculate percentages for each course
        for course in course_stats:
            stats = course_stats[course]
            total = stats['total']
            if total > 0:
                stats['present_percentage'] = (stats['present'] / total * 100)
                stats['late_percentage'] = (stats['late'] / total * 100)
                stats['absent_percentage'] = (stats['absent'] / total * 100)
                stats['attendance_percentage'] = ((stats['present'] + stats['late']) / total * 100)
        
        context = {
            'total_classes': total_classes,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'attendance_percentage': round(attendance_percentage, 1),
            'status': status,
            'status_class': status_class,
            'course_stats': course_stats,
        }
        return render(request, 'StudentView/attendance_report.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('student_login')
