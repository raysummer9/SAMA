# QR Code-Based Attendance System

A Django-based web application for managing student attendance using QR codes. This system provides separate interfaces for faculty and students, making attendance tracking efficient and automated.

## Features

### Faculty Features
- Secure login system for faculty members
- Create and manage courses
- Generate QR codes for attendance sessions
- View and manage attendance records
- Export attendance data
- Real-time attendance tracking

### Student Features
- Student login system
- Scan QR codes to mark attendance
- View personal attendance history
- Access course information

## Prerequisites

- Python 3.x
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd QR-Attendance-System
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create a superuser (admin account):
```bash
python manage.py createsuperuser
```

## Running the Application

### Development Server
To run the application locally:
```bash
python manage.py runserver
```
The application will be available at `http://127.0.0.1:8000/`

### With Ngrok (for external access)
The project includes support for ngrok to make the application accessible from outside your local network:
```bash
python run_with_ngrok.py
```
Note: You'll need to have ngrok installed and configured with your authentication token.

## Usage

### Faculty Access
1. Navigate to `/faculty/login/`
2. Log in with your faculty credentials
3. Create courses and manage attendance sessions
4. Generate QR codes for attendance tracking

### Student Access
1. Navigate to `/student/login/`
2. Log in with your student credentials
3. Access your courses and attendance records
4. Scan QR codes during attendance sessions

## Project Structure

```
QR-Attendance-System/
├── FacultyView/           # Faculty-specific views and models
├── StudentView/          # Student-specific views and models
├── QR_Attendance_System/ # Main project settings
├── templates/            # HTML templates
├── static/              # Static files (CSS, JS, images)
├── manage.py            # Django management script
└── requirements.txt     # Project dependencies
```

## Dependencies

- Django: Web framework
- qrcode: QR code generation
- pillow: Image processing
- pyngrok: For external access (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the development team.
