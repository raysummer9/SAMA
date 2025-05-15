from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require authentication
        public_urls = [
            reverse('faculty_login'),
            '/admin/login/',
            '/admin/',
            reverse('student_login'),
            '/student/mark-attendance/',
        ]

        # Check if the current path is in public_urls
        if not any(request.path.startswith(url) for url in public_urls):
            # Check if it's a faculty URL
            if request.path.startswith('/faculty/'):
                if not request.user.is_authenticated:
                    messages.warning(request, 'Please log in to access this page.')
                    return redirect('faculty_login')
            # Check if it's a student URL
            elif request.path.startswith('/student/'):
                if not request.session.get('student_id'):
                    messages.warning(request, 'Please log in to access this page.')
                    return redirect('student_login')

        response = self.get_response(request)
        return response 