from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from .models import Student, FacultyUser, Course, Attendance, AttendanceSession
from StudentView.views import present
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import FacultyLoginForm, StudentRegistrationForm, CourseForm, AttendanceForm, AttendanceSessionForm
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import qrcode
import socket
import os
import csv


def qrgenerator():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]

    link = f"http://{ip}:8000/add_manually"

    # Function to generate and display a QR code
    def generate_qr_code(link):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("FacultyView/static/FacultyView/qrcode.png")

    generate_qr_code(link)


def faculty_view(request):
    if request.method == "POST":
        student_roll = request.POST["student_id"]
        student = Student.objects.get(s_roll=student_roll)
        if student in present:
            present.remove(student)
        return HttpResponseRedirect("/")

    else:
        qrgenerator()
        return render(
            request,
            "FacultyView/FacultyViewIndex.html",
            {
                "students": present,
            },
        )


def add_manually(request):
    students = Student.objects.all().order_by("s_roll")
    return render(
        request,
        "StudentView/StudentViewIndex.html",
        {
            "students": students,
        },
    )


def login_view(request):
    print("="*50)
    print("Login view called")
    print(f"Request method: {request.method}")
    print(f"Request POST data: {request.POST}")
    print("="*50)
    
    # Check if user was redirected due to session expiry
    if request.GET.get('next'):
        messages.warning(request, 'Your session has expired. Please log in again.')
    
    if request.method == 'POST':
        form = FacultyLoginForm(request.POST)
        print(f"Form is valid: {form.is_valid()}")
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            print(f"Attempting to authenticate user with email: {email}")
            
            try:
                user = FacultyUser.objects.get(email=email)
                if user.check_password(password):
                    print("User authenticated successfully")
                    login(request, user)
                    # Redirect to the next page if it exists, otherwise to dashboard
                    next_url = request.GET.get('next', 'faculty_dashboard')
                    return redirect(next_url)
                else:
                    print("Authentication failed - invalid password")
                    messages.error(request, 'Invalid email or password.')
            except FacultyUser.DoesNotExist:
                print("User not found")
                messages.error(request, 'Invalid email or password.')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = FacultyLoginForm()
    return render(request, 'FacultyView/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('faculty_login')


@login_required
def dashboard(request):
    faculty = request.user
    courses = Course.objects.filter(faculty=faculty)
    students = Student.objects.all()  # Count all students
    
    # Only show attendance records from actual attendance sessions
    recent_attendance = Attendance.objects.filter(
        course__in=courses,
        date=timezone.now().date(),
        session__isnull=False  # Only show records from actual sessions
    ).select_related('student', 'course', 'session').order_by('-created_at')[:5]
    
    context = {
        'courses': courses,
        'students': students,
        'recent_attendance': recent_attendance,
    }
    return render(request, 'FacultyView/dashboard.html', context)


@login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            student = form.save()
            print(f"Created student: {student.name} (ID: {student.id})")
            
            # Get all existing courses
            all_courses = Course.objects.all()
            print(f"Found {all_courses.count()} courses")
            
            # Create attendance records for each course
            for course in all_courses:
                print(f"Creating attendance record for course: {course.name}")
                attendance = Attendance.objects.create(
                    student=student,
                    course=course,
                    date=timezone.now().date(),
                    status='absent',  # Default status for new enrollments
                    session=None  # No session for initial enrollment
                )
                print(f"Created attendance record: {attendance.id}")
            
            # Verify records were created
            created_records = Attendance.objects.filter(student=student).count()
            print(f"Total attendance records created: {created_records}")
            
            messages.success(request, 'Student added successfully!')
            return redirect('faculty_dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'FacultyView/add_student.html', {'form': form})


@login_required
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.faculty = request.user
            course.save()
            
            # Get all existing students
            all_students = Student.objects.all()
            print(f"Found {all_students.count()} students")
            
            # Create attendance records for each student
            for student in all_students:
                print(f"Creating attendance record for student: {student.name}")
                attendance = Attendance.objects.create(
                    student=student,
                    course=course,
                    date=timezone.now().date(),
                    status='absent',  # Default status for new enrollments
                    session=None  # No session for initial enrollment
                )
                print(f"Created attendance record: {attendance.id}")
            
            messages.success(request, 'Course added successfully!')
            return redirect('faculty_dashboard')
    else:
        form = CourseForm()
    return render(request, 'FacultyView/add_course.html', {'form': form})


@login_required
def mark_attendance(request):
    if request.method == 'POST':
        form = AttendanceSessionForm(request.POST, faculty=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            
            # Generate QR code for the session
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # Higher error correction
                box_size=20,  # Larger box size
                border=4,
            )
            
            # Get the current host from the request
            host = request.get_host()
            # Create URL for students to mark attendance
            attendance_url = f"http://{host}/student/mark-attendance/{str(session.session_code)}/"
            print(f"Generated QR code URL: {attendance_url}")  # Debug print
            
            qr.add_data(attendance_url)
            qr.make(fit=True)
            
            # Save QR code image with higher resolution
            img = qr.make_image(fill_color="black", back_color="white")
            # Ensure the directory exists
            os.makedirs("FacultyView/static/FacultyView/qrcodes", exist_ok=True)
            qr_path = f"FacultyView/static/FacultyView/qrcodes/session_{session.session_code}.png"
            img.save(qr_path)
            
            messages.success(request, 'Attendance session created successfully!')
            return redirect('view_attendance_session', session_id=session.session_code)
    else:
        form = AttendanceSessionForm(faculty=request.user)
    
    return render(request, 'FacultyView/create_attendance.html', {'form': form})


@login_required
def view_attendance_session(request, session_id):
    try:
        session = AttendanceSession.objects.get(
            session_code=session_id,
            created_by=request.user
        )
        attendance_records = Attendance.objects.filter(session=session)
        
        context = {
            'session': session,
            'attendance_records': attendance_records,
            'qr_code_url': f'/static/FacultyView/qrcodes/session_{session.session_code}.png'
        }
        return render(request, 'FacultyView/view_attendance_session.html', context)
    except AttendanceSession.DoesNotExist:
        messages.error(request, 'Attendance session not found.')
        return redirect('faculty_dashboard')


@login_required
def attendance_history(request):
    active_sessions = AttendanceSession.objects.filter(created_by=request.user, is_active=True).order_by('-created_at')
    expired_sessions = AttendanceSession.objects.filter(created_by=request.user, is_active=False).order_by('-created_at')
    return render(request, 'FacultyView/attendance_history.html', {
        'active_sessions': active_sessions,
        'expired_sessions': expired_sessions
    })


@login_required
def view_all_students(request):
    students = Student.objects.all().order_by('name')
    return render(request, 'FacultyView/view_all_students.html', {'students': students})


# Add a new view for listing active and expired sessions
@login_required
def list_attendance_sessions(request):
    active_sessions = AttendanceSession.objects.filter(created_by=request.user, is_active=True).order_by('-created_at')
    expired_sessions = AttendanceSession.objects.filter(created_by=request.user, is_active=False).order_by('-created_at')
    return render(request, 'FacultyView/list_attendance_sessions.html', {
        'active_sessions': active_sessions,
        'expired_sessions': expired_sessions
    })


# Add a new view to end an active session
@login_required
def end_attendance_session(request, session_id):
    try:
        session = AttendanceSession.objects.get(
            session_code=session_id,
            created_by=request.user,
            is_active=True
        )
        
        # Get all students enrolled in the course through the courses relationship
        enrolled_students = Student.objects.filter(
            courses__id=session.course.id
        ).distinct()
        
        # Get students who have already marked attendance
        marked_students = Attendance.objects.filter(
            session=session
        ).values_list('student_id', flat=True)
        
        # Find students who haven't marked attendance
        absent_students = enrolled_students.exclude(id__in=marked_students)
        
        # Create absent records for students who haven't marked attendance
        absent_records = [
            Attendance(
                student=student,
                course=session.course,
                session=session,
                date=session.date,
                status='absent'
            )
            for student in absent_students
        ]
        
        # Bulk create absent records
        if absent_records:
            Attendance.objects.bulk_create(absent_records)
        
        # End the session
        session.is_active = False
        session.save()
        
        messages.success(request, f'Attendance session ended successfully. {len(absent_records)} students marked as absent.')
    except AttendanceSession.DoesNotExist:
        messages.error(request, 'Attendance session not found or already ended.')
    return redirect('list_attendance_sessions')


@login_required
def remove_student(request, student_id):
    print(f"Attempting to remove student with ID: {student_id}")
    print(f"Request method: {request.method}")
    
    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            print(f"Found student: {student.name} (ID: {student.id})")
            
            # Delete all attendance records for this student first
            attendance_records = Attendance.objects.filter(student=student)
            print(f"Deleting {attendance_records.count()} attendance records")
            attendance_records.delete()
            
            # Now delete the student
            student_name = student.name
            student.delete()
            print(f"Successfully deleted student: {student_name}")
            
            messages.success(request, f'Student {student_name} has been removed successfully.')
        except Student.DoesNotExist:
            print(f"Student with ID {student_id} not found")
            messages.error(request, 'Student not found.')
        except Exception as e:
            print(f"Error removing student: {str(e)}")
            messages.error(request, f'Error removing student: {str(e)}')
    else:
        print(f"Invalid request method: {request.method}")
        messages.error(request, 'Invalid request method.')
    
    return redirect('view_all_students')


@login_required
def attendance_report(request):
    # Get filter parameters
    filter_type = request.GET.get('filter', 'today')
    course_id = request.GET.get('course')
    student_id = request.GET.get('student')
    status = request.GET.get('status')
    
    # Get base queryset for the faculty's courses
    base_queryset = Attendance.objects.filter(
        course__faculty=request.user,
        session__isnull=False  # Only include records from actual sessions
    ).select_related('student', 'course', 'session')
    
    # Apply date filtering
    today = timezone.now().date()
    if filter_type == 'today':
        queryset = base_queryset.filter(date=today)
    elif filter_type == 'week':
        week_ago = today - timedelta(days=7)
        queryset = base_queryset.filter(date__gte=week_ago)
    elif filter_type == 'month':
        month_ago = today - timedelta(days=30)
        queryset = base_queryset.filter(date__gte=month_ago)
    else:
        queryset = base_queryset
    
    # Apply additional filters
    if course_id:
        queryset = queryset.filter(course_id=course_id)
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    if status:
        queryset = queryset.filter(status=status)
    
    # Order by date and time
    queryset = queryset.order_by('-date', '-created_at')
    
    # Get filter options for the template
    courses = Course.objects.filter(faculty=request.user).order_by('code')
    students = Student.objects.filter(
        courses__faculty=request.user
    ).distinct().order_by('name')
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_report_{filter_type}_{today}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Student Name', 'Matric Number', 'Course', 'Date', 'Lecture Time', 'Scan Time', 'Status'])
        
        for record in queryset:
            writer.writerow([
                record.student.name,
                record.student.matric_number,
                f"{record.course.code} - {record.course.name}",
                record.date,
                record.session.start_time.strftime('%I:%M %p'),
                record.created_at.strftime('%I:%M %p'),
                record.status.capitalize()
            ])
        
        return response
    
    # Pagination for web view
    paginator = Paginator(queryset, 7)  # 7 records per page
    page_number = request.GET.get('page', 1)
    attendance_records = paginator.get_page(page_number)
    
    context = {
        'attendance_records': attendance_records,
        'filter': filter_type,
        'courses': courses,
        'students': students,
        'selected_course': course_id,
        'selected_student': student_id,
        'selected_status': status,
    }
    return render(request, 'FacultyView/attendance_report.html', context)


@login_required
def student_attendance_report(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        
        # Get all attendance records for this student in the faculty's courses
        attendance_records = Attendance.objects.filter(
            student=student,
            course__faculty=request.user,
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
            'student': student,
            'total_classes': total_classes,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'attendance_percentage': round(attendance_percentage, 1),
            'status': status,
            'status_class': status_class,
            'course_stats': course_stats,
        }
        return render(request, 'FacultyView/student_attendance_report.html', context)
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('faculty_dashboard')
