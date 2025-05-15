import os
from pyngrok import ngrok
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    # Open a ngrok tunnel to the Django development server
    public_url = ngrok.connect(8000).public_url
    print(f' * ngrok tunnel "{public_url}" -> http://127.0.0.1:8000')

    # Update Django settings to allow the ngrok domain
    os.environ['DJANGO_SETTINGS_MODULE'] = 'QR_Attendance_System.settings'
    os.environ['ALLOWED_HOSTS'] = '*'

    # Run the Django development server
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000']) 