# SKILdemy

A comprehensive online learning platform designed to teach skills through structured courses with multimedia content, AI-powered features, and multi-language support.

## Features

### Course Management
- Hierarchical course structure: **Courses → Topics → Subtopics**
- Create, update, and delete courses with descriptions and pricing
- Free trial access to selected course content
- Course ratings and student enrollment tracking
- Discount management for promotional pricing

### User Experience
- User registration, authentication, and profile management
- Role-based access (Students, Moderators, Administrators)
- Multi-language support (13+ languages: Arabic, Bengali, German, Spanish, French, Hindi, Indonesian, Japanese, Korean, Portuguese, Russian, Turkish, Urdu, Chinese)
- Personalized learning dashboards
- Password reset via email verification

### Content Features
- **Video Management**: Upload, process, and stream course videos
- **AI-Generated Content**: Automatic video and content generation using AI
- **Text-to-Speech**: Convert reading materials to audio (gTTS)
- **Translation**: AI-powered content translation across supported languages
- **Code Exercises**: Upload and manage code assignments with output tracking
- **Certificates**: Generate completion certificates for finished courses
- **Reading Materials**: Structured text content with display management

### Learning & Assessment
- Time-based learning tasks
- User submissions and solution tracking
- Progress monitoring across subtopics
- Certificate generation and viewing

### Payment & Business
- Stripe integration for course payments
- Secure transaction handling
- Enrollment management

## Technology Stack

### Backend
- **Framework**: Flask 2.3.3
- **Python ORM**: SQLAlchemy
- **Database**: SQLite (primary), MongoDB (video metadata)
- **Authentication**: Flask-Login, Bcrypt
- **Email**: Flask-Mail (SMTP - Gmail)
- **Internationalization**: Babel

### Frontend
- **CSS Framework**: Bootstrap
- **Template Engine**: Jinja2
- **JavaScript**: Vanilla JS with Bootstrap Bundle

### Additional Libraries
- **Video Processing**: MoviePy
- **AI/Translation**: Google Translate, gTTS
- **Security**: Flask-WTF (CSRF), Flask-Limiter (rate limiting)
- **Database Migration**: Alembic, Flask-Migrate
- **AWS**: Boto3 (S3 integration)
- **Validation**: WTForms, email-validator

## Installation

### Prerequisites
- Python 3.8+
- MongoDB Atlas account (for video metadata)
- Gmail account (for email notifications)
- Stripe account (for payments)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SKILdemy
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   MONGO_URI=your_mongodb_connection_string
   MAIL_USERNAME=your_gmail
   MAIL_PASSWORD=your_app_password
   SECRET_KEY=your_secret_key
   ```

5. **Initialize database**
   ```bash
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

## Project Structure

```
SKILdemy/
├── app.py                          # Application entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── instance/                       # Instance folder (configs, db)
├── migrations/                     # Database migrations (Alembic)
├── output_folder/                  # Generated files output
└── learning_platform/              # Main application package
    ├── __init__.py                # Flask app initialization
    ├── _helpers.py                # Utility functions
    ├── babel.cfg                  # Babel config for i18n
    ├── google_translations.py      # Translation utilities
    ├── forms/
    │   └── form.py               # WTForms definitions
    ├── models/
    │   └── models.py             # SQLAlchemy models
    ├── views/
    │   ├── home.py               # Home page routes
    │   ├── users.py              # User auth & profile routes
    │   └── admin.py              # Admin management routes
    ├── static/                    # Static assets
    │   ├── css/                  # Stylesheets
    │   ├── js/                   # JavaScript files
    │   ├── certificate/          # Generated certificates
    │   ├── myvideo/              # Course videos
    │   ├── thumbnail/            # Course thumbnails
    │   ├── user_output/          # User submissions
    │   └── video_lists/          # Video management
    ├── templates/                 # Jinja2 HTML templates
    │   ├── base.html             # Base template
    │   ├── home/                 # Home page templates
    │   ├── user/                 # User-facing templates
    │   ├── admin/                # Admin templates
    │   ├── content_management/   # Course editing templates
    │   └── payment/              # Payment templates
    └── translations/              # i18n translations
        ├── ar, bn, de, es, fr, hi, id, ja, ko, pt, ru, tr, ur, zh_CN/
```

## Database Models

### User
- Profile management and authentication
- Course enrollments (many-to-many)
- Time tasks and solutions tracking

### Course
- Course metadata (name, description, price)
- Topics association (many-to-many)
- Enrollment history

### Topic & SubTopic
- Hierarchical course content
- Reading materials and video content
- User solutions tracking

### Payment
- Transaction records
- Enrollment tracking

## Key Features Implementation

### Multi-Language Support
The application uses Babel for internationalization. Add translations via:
```bash
pybabel extract -F learning_platform/babel.cfg -o learning_platform/messages.pot learning_platform/
pybabel init -i learning_platform/messages.pot -d learning_platform/translations -l <language_code>
```

### Rate Limiting
Default: 7 requests per second per IP address. Configure in `learning_platform/__init__.py`

### Security
- CSRF protection enabled via Flask-WTF
- Passwords hashed with Bcrypt
- Session timeout: 120 minutes

## Usage

### For Students
1. Register an account
2. Browse available courses
3. Enroll in free or paid courses
4. Watch videos and complete exercises
5. Submit solutions and earn certificates

### For Instructors/Admins
1. Login with admin credentials
2. Create courses and organize content into topics/subtopics
3. Upload videos or generate AI content
4. Translate content to multiple languages
5. Monitor student progress

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is proprietary. All rights reserved.

## Support

For issues, questions, or suggestions, please open an issue in the repository or contact the development team.

---

**SKILdemy** - Empowering learners worldwide with accessible, multilingual skill education.
