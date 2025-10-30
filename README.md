# Django Chat Application

A full-featured real-time chat application built with Django, Django Channels, and WebSockets.

## Features

### Core Features
- ✅ **User Authentication** - Complete signup/login system with secure password handling
- ✅ **Real-time Messaging** - WebSocket-based instant messaging using Django Channels
- ✅ **Multiple Chat Rooms** - Support for both group chats and private one-on-one conversations
- ✅ **Message Storage** - Persistent storage of text messages with support for images and files
- ✅ **RESTful API** - Full-featured REST API built with Django REST Framework
- ✅ **Responsive Frontend** - Bootstrap 5-based responsive templates
- ✅ **Admin Panel** - Comprehensive Django admin interface for managing users, rooms, and messages

### Additional Features
- User profiles with avatars and bio
- Online/offline status tracking
- Typing indicators in real-time
- Room membership management with roles (Admin, Moderator, Member)
- Message read receipts
- File and image uploads
- Search and filter functionality
- JWT authentication for API
- CORS support for frontend integration

## Technology Stack

- **Backend**: Django 4.2
- **Real-time**: Django Channels 4.0 with Redis
- **API**: Django REST Framework 3.14
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **Frontend**: Bootstrap 5, JavaScript (WebSocket)
- **Authentication**: Django Allauth, JWT
- **File Storage**: Django's FileField with PIL for images

## Project Structure

```
chat-app-django/
├── accounts/              # User authentication and profile management
│   ├── models.py         # Custom User model
│   ├── views.py          # Login, signup, profile views
│   └── admin.py          # User admin configuration
├── chat/                  # Chat functionality
│   ├── models.py         # ChatRoom, Message, RoomMembership models
│   ├── views.py          # Chat room views
│   ├── consumers.py      # WebSocket consumers
│   ├── routing.py        # WebSocket URL routing
│   └── admin.py          # Chat admin configuration
├── api/                   # REST API
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # API viewsets
│   └── urls.py           # API URL configuration
├── chatapp/              # Project settings
│   ├── settings.py       # Django settings with security best practices
│   ├── asgi.py          # ASGI configuration for Channels
│   └── urls.py          # Main URL configuration
├── templates/            # HTML templates
│   ├── base/            # Base templates
│   ├── accounts/        # Authentication templates
│   └── chat/            # Chat templates
├── static/              # Static files (CSS, JS, images)
├── media/               # User-uploaded files
├── requirements.txt     # Python dependencies
└── manage.py           # Django management script
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Redis server (for Channels)
- pip (Python package installer)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/anuragx02/chat-app-django.git
   cd chat-app-django
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Start Redis** (in a separate terminal)
   ```bash
   redis-server
   ```

9. **Run the development server**
   ```bash
   python manage.py runserver
   # Or use Daphne for ASGI:
   daphne -b 0.0.0.0 -p 8000 chatapp.asgi:application
   ```

10. **Access the application**
    - Web Interface: http://localhost:8000
    - Admin Panel: http://localhost:8000/admin
    - API: http://localhost:8000/api

## Usage

### Web Interface

1. **Sign Up**: Create a new account at `/accounts/signup/`
2. **Login**: Login at `/accounts/login/`
3. **Lobby**: View all your chat rooms at `/chat/`
4. **Create Room**: Create a new chat room at `/chat/create/`
5. **Join Chat**: Click on any room to start chatting
6. **Private Chat**: Click on a user to start a private conversation

### REST API

The API is available at `/api/` with the following endpoints:

- **Authentication**
  - `POST /api/token/` - Obtain JWT token
  - `POST /api/token/refresh/` - Refresh JWT token

- **Users**
  - `GET /api/users/` - List users
  - `GET /api/users/me/` - Get current user
  - `PATCH /api/users/{id}/update_profile/` - Update profile

- **Rooms**
  - `GET /api/rooms/` - List user's rooms
  - `POST /api/rooms/` - Create new room
  - `GET /api/rooms/{id}/` - Get room details
  - `POST /api/rooms/{id}/join/` - Join room
  - `POST /api/rooms/{id}/leave/` - Leave room
  - `GET /api/rooms/{id}/members/` - List room members

- **Messages**
  - `GET /api/messages/?room_id={id}` - List messages in room
  - `POST /api/messages/` - Send message
  - `PATCH /api/messages/{id}/edit/` - Edit message
  - `POST /api/messages/{id}/mark_read/` - Mark message as read

### WebSocket Connection

Connect to WebSocket for real-time messaging:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/{room_slug}/');
```

## Security Features

- Secret key management with environment variables
- CSRF protection
- XSS protection (X-XSS-Protection header)
- Content type sniffing protection
- Clickjacking protection (X-Frame-Options)
- Secure cookies in production
- SSL redirect in production
- Password validation
- File upload validation and size limits
- User permission checks for all operations

## API Authentication

The API supports three authentication methods:
1. **Session Authentication** - For browser-based clients
2. **Token Authentication** - For mobile/desktop apps
3. **JWT Authentication** - For modern single-page applications

## Configuration

### Environment Variables

Key environment variables in `.env`:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `REDIS_HOST` - Redis server host
- `REDIS_PORT` - Redis server port
- `CORS_ALLOWED_ORIGINS` - CORS allowed origins

### File Upload Limits

Configure in `settings.py`:
- `MAX_IMAGE_SIZE` - Maximum image size (default: 5MB)
- `MAX_FILE_SIZE` - Maximum file size (default: 10MB)
- `ALLOWED_IMAGE_EXTENSIONS` - Allowed image formats
- `ALLOWED_FILE_EXTENSIONS` - Allowed file formats

## Admin Panel

Access the admin panel at `/admin/` with superuser credentials.

Features:
- User management (view, edit, delete users)
- Room management (create, modify, delete rooms)
- Message moderation (view, delete messages)
- Membership management (add/remove members, change roles)
- System monitoring and statistics

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
Follow PEP 8 guidelines for Python code.

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Production Deployment

### PostgreSQL Setup
1. Install PostgreSQL
2. Create database
3. Update `DATABASES` in settings.py
4. Run migrations

### Redis Setup
1. Install Redis
2. Update `CHANNEL_LAYERS` in settings.py

### Security Checklist
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS
- [ ] Set secure cookies
- [ ] Configure proper database
- [ ] Set up Redis for production
- [ ] Configure file storage (S3, etc.)
- [ ] Set up proper logging
- [ ] Configure firewall
- [ ] Use environment variables for secrets

### Deployment Options
- **Heroku**: Use Procfile with Daphne
- **AWS**: EC2 with Nginx + Daphne
- **Docker**: Containerize with docker-compose
- **DigitalOcean**: App Platform or Droplet

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Credits

Built with:
- Django - Web framework
- Django Channels - WebSocket support
- Django REST Framework - API
- Bootstrap - UI framework
- Redis - Message broker
