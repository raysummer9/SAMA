from django.core.management.base import BaseCommand
from FacultyView.models import Student, Course, Attendance
from django.utils import timezone

class Command(BaseCommand):
    help = 'Syncs all students with all courses by creating attendance records'

    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        courses = Course.objects.all()
        
        self.stdout.write(f"Found {students.count()} students and {courses.count()} courses")
        
        for student in students:
            for course in courses:
                # Check if attendance record already exists
                if not Attendance.objects.filter(student=student, course=course).exists():
                    Attendance.objects.create(
                        student=student,
                        course=course,
                        date=timezone.now().date(),
                        status='absent',
                        session=None
                    )
                    self.stdout.write(f"Created attendance record for {student.name} in {course.name}")
        
        self.stdout.write(self.style.SUCCESS('Successfully synced all students with all courses')) 