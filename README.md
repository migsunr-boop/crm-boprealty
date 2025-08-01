# Real Estate CRM with TATA Chat Panel Integration

A comprehensive Django-based CRM system for real estate businesses with integrated TATA WhatsApp and RCS messaging capabilities.

## 🚀 Features

### Core CRM Features
- **Dashboard** - Overview of leads, projects, and analytics
- **Project Management** - Manage real estate projects with images and details
- **Lead Management** - Track leads through different stages
- **Team Management** - User roles and permissions
- **Calendar & Tasks** - Schedule meetings and manage tasks
- **Reports & Analytics** - Comprehensive business insights
- **Client Management** - Maintain client relationships

### TATA Integration Features
- **WhatsApp Business API** - Send template and session messages
- **RCS Messaging** - Rich Communication Services
- **Chat Panel** - Unified inbox for all conversations
- **Webhook Support** - Real-time message handling
- **Bulk Messaging** - Email, WhatsApp, and SMS campaigns
- **Media Management** - Upload and manage media files

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Django 4.2+
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/anant114work/crm.git
   cd crm
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

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run the server**
   ```bash
   python manage.py runserver
   ```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# TATA API Configuration
TATA_AUTH_TOKEN=your-tata-auth-token-here
TATA_BASE_URL=https://wb.omni.tatatelebusiness.com
```

### TATA Webhook Setup

1. **Configure webhook URL in TATA panel:**
   ```
   https://yourdomain.com/webhook/
   ```

2. **For local development with ngrok:**
   ```bash
   ngrok http 8000
   # Use the ngrok URL: https://abc123.ngrok.io/webhook/
   ```

## 📱 TATA Chat Panel Usage

### Accessing the Chat Panel
- Navigate to `/tata-chat/` in your browser
- Or click "TATA Chat Panel" in the sidebar

### Features
- **Real-time messaging** - View and reply to WhatsApp/RCS messages
- **Conversation management** - Organize chats by phone number
- **Auto-refresh** - Updates every 10 seconds
- **Export functionality** - Download chat history
- **Mobile responsive** - Works on all devices

### API Integration
The system integrates with:
- **WhatsApp Business API** - Template and session messages
- **RCS API** - Rich messaging capabilities
- **Webhook handling** - Real-time message reception

## 🔧 API Endpoints

### TATA Chat Panel APIs
- `GET /tata-chat/` - Chat panel interface
- `GET /ajax/tata-conversations/` - Get all conversations
- `POST /ajax/tata-send-reply/` - Send reply to customer
- `POST /webhook/` - Webhook for incoming messages

### Core CRM APIs
- `GET /` - Dashboard
- `GET /projects/` - Project management
- `GET /leads/` - Lead management
- `GET /team/` - Team management
- `GET /calendar/` - Calendar and events
- `GET /tasks/` - Task management

## 🏗️ Project Structure

```
crm/
├── dashboard/              # Main Django app
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py            # URL routing
│   ├── chat_panel.py      # TATA chat integration
│   └── migrations/        # Database migrations
├── templates/             # HTML templates
│   └── dashboard/         # Dashboard templates
├── static/               # Static files (CSS, JS, images)
├── media/                # User uploaded files
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── manage.py            # Django management script
```

## 🔐 Security Features

- **User Authentication** - Django's built-in auth system
- **Role-based Permissions** - Team member access control
- **CSRF Protection** - Cross-site request forgery protection
- **Webhook Validation** - Secure webhook payload verification
- **Environment Variables** - Sensitive data protection

## 📊 Database Models

### Core Models
- **Project** - Real estate projects
- **Lead** - Customer leads with stages
- **TeamMember** - User roles and permissions
- **Task** - Task management
- **CalendarEvent** - Meetings and events
- **Client** - Customer information

### TATA Integration Models
- **WhatsAppTemplate** - Message templates
- **WhatsAppMessage** - Message history
- **IVRCallLog** - Call logs from TATA IVR

## 🚀 Deployment

### Production Setup

1. **Set environment variables**
   ```env
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com
   ```

2. **Configure database** (PostgreSQL recommended)
   ```env
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

3. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

4. **Use production server**
   ```bash
   gunicorn realty_dashboard.wsgi:application
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Email: support@yourcompany.com

## 🔄 Updates

### Latest Version Features
- ✅ TATA WhatsApp Business API integration
- ✅ RCS messaging support
- ✅ Real-time chat panel
- ✅ Webhook handling
- ✅ Bulk messaging capabilities
- ✅ Media management
- ✅ Advanced analytics
- ✅ Team hierarchy management

---

**Built with ❤️ for Real Estate Professionals**