# 🚀 TripAI - AI-Powered Travel Itinerary Generator

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14+-blue.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

A professional Django web application that generates personalized travel itineraries using AI (OpenAI GPT) and Google Maps APIs. Features cost optimization, intelligent caching, OAuth2 authentication, and a comprehensive REST API built with Django REST Framework.

## ✨ Features

- 🤖 **AI-Powered Planning**: GPT-4/5 integration for intelligent trip planning
- 🗺️ **Location Intelligence**: Google Maps API for locations, photos, and directions
- 💰 **Cost Optimization**: Real-time API cost monitoring and intelligent caching
- 📄 **PDF Generation**: Beautiful trip itinerary PDFs with images and maps
- 🔐 **OAuth2 Authentication**: Secure Google OAuth2 integration
- 📊 **Admin Dashboard**: Real-time cost monitoring and analytics
- 🚀 **REST API**: Comprehensive DRF-based API (JWT-ready)
- ⚡ **Performance**: Intelligent caching and cost-optimized API calls
- 🧪 **Testing**: Comprehensive test coverage with pytest
- 📱 **Responsive**: Mobile-friendly design

## 🚀 Quick Start

### For DRF/JWT Experts (Fast Track)

```bash
# Clone and setup
git clone <repository-url> && cd trip-django
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Environment setup
cp .env.example .env
# Add your API keys to .env

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Test the API
python tests/test_runner.py api

# Start development
python manage.py runserver
```

**Key DRF files**: `home/api_views.py`, `home/serializers.py`, `tests/integration/test_api_endpoints.py`

### Standard Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trip-django
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key
   DJANGO_SECRET_KEY=your-secret-key
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run the application**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Web Interface: http://127.0.0.1:8000
   - API Documentation: http://127.0.0.1:8000/api/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - Cost Dashboard: http://127.0.0.1:8000/cost-dashboard/ (superuser only)

## 📁 Project Structure

```
trip-django/
├── 🔥 home/                         # Main Django app
│   ├── api_views.py                # DRF API endpoints
│   ├── serializers.py              # DRF serializers
│   ├── models.py                   # Database models
│   ├── optimized_services.py       # Cost-optimized APIs
│   ├── cost_monitor.py             # Cost tracking
│   └── management/commands/        # Custom commands
├── 🔥 tests/                       # Comprehensive tests
│   ├── integration/                # API tests
│   ├── unit/                      # Unit tests
│   └── functional/                # End-to-end tests
├── 🔥 docs/                        # Documentation
│   ├── development/               # Dev guides
│   └── deployment/                # Deployment docs
├── templates/                      # Global templates
├── static/                         # Static files
├── scripts/                        # Utility scripts
└── logs/                          # Application logs

🔥 = Critical directories for developers
```

For detailed project structure explanation, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🔌 API Documentation

### Authentication

```http
# Token Authentication (Current)
Authorization: Token <your-token>

# JWT Authentication (Ready for migration)
Authorization: Bearer <jwt-token>
```

### Core Endpoints

```http
# Trip Management
GET    /api/trip-status/<id>/        # Check generation status
POST   /api/generate-pdf/<id>/       # Generate PDF

# Location Services
GET    /api/autocomplete/?query=Paris         # Location search
GET    /api/location-photos/?location=Eiffel  # Get photos

# Admin (Superuser only)
GET    /api/cost-monitor/             # Cost dashboard data
```

### Example API Usage

```bash
# Get location suggestions
curl -H "Authorization: Token <your-token>" \
     "http://127.0.0.1:8000/api/autocomplete/?query=Paris"

# Check trip status
curl -H "Authorization: Token <your-token>" \
     "http://127.0.0.1:8000/api/trip-status/123/"
```

## 🧪 Testing

### Run Tests

```bash
# All tests
python manage.py test

# Specific test categories
python tests/test_runner.py unit        # Unit tests
python tests/test_runner.py integration # API tests
python tests/test_runner.py functional  # E2E tests
python tests/test_runner.py api         # DRF-specific tests

# With coverage
pytest tests/ --cov=home --cov-report=html
```

### Test Coverage
- **API Endpoints**: 100%
- **Serializers**: 95%
- **Models**: 90%
- **Services**: 85%

## 🔐 JWT Migration

The project is **JWT-ready**! To enable JWT authentication:

```bash
# 1. Install JWT package
pip install djangorestframework-simplejwt

# 2. Uncomment JWT configuration in main/settings.py (lines 232-234, 261-273)

# 3. Update frontend to use Bearer tokens
```

Detailed JWT migration guide: [docs/development/DEVELOPER_ONBOARDING.md](docs/development/DEVELOPER_ONBOARDING.md#jwt-migration)

## 💰 Cost Optimization

### Built-in Cost Controls
- **Intelligent Caching**: 7-day cache for Google Maps, 3-day cache for AI responses
- **API Call Limits**: Configurable daily limits and monitoring
- **Optimized Models**: GPT-4o-mini for cost efficiency, GPT-5 for quality
- **Real-time Monitoring**: Live cost dashboard with recommendations

### Cost Dashboard

Access at `/cost-dashboard/` (superuser only) for:
- Daily/hourly API usage statistics
- Cost breakdown by service
- Cache hit/miss rates
- Optimization recommendations

## 🛠️ Development

### For DRF/JWT Experts

**Priority files to examine**:
1. `home/api_views.py` - Main API implementation
2. `home/serializers.py` - DRF serializers with JWT patterns
3. `tests/integration/test_api_endpoints.py` - API testing patterns
4. `main/settings.py` - DRF configuration

**Development opportunities**:
- JWT migration (2-minute setup)
- ViewSets implementation
- API versioning
- Advanced permissions
- WebSocket integration

### Management Commands

```bash
# Populate sample destinations
python manage.py populate_destinations

# Regenerate PDF for specific trip
python manage.py regenerate_pdf <trip_id>

# Setup Google OAuth
python manage.py setup_google_oauth
```

### Environment Variables

```env
# Required
OPENAI_API_KEY=your-openai-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
DJANGO_SECRET_KEY=your-secret-key

# Optional
OPENAI_MODEL=gpt-4o  # or gpt-5
TEMPERATURE=1.0
MAX_TOKENS=4000
DEBUG=True

# Database (optional - uses SQLite by default)
DB_NAME=tripai_db
DB_USER=postgres
DB_PASSWORD=your-password

# OAuth (optional)
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
```

## 🚀 Deployment

### Production Environment

1. **Environment Setup**
   ```bash
   export DEBUG=False
   export ALLOWED_HOSTS=your-domain.com
   ```

2. **Database Migration**
   ```bash
   python manage.py migrate --settings=main.settings.production
   ```

3. **Static Files**
   ```bash
   python manage.py collectstatic --no-input
   ```

4. **Run with Gunicorn**
   ```bash
   gunicorn main.wsgi:application
   ```

Detailed deployment guide: [docs/deployment/DEPLOYMENT_CHECKLIST.md](docs/deployment/DEPLOYMENT_CHECKLIST.md)

## 📊 Architecture

### Technology Stack
- **Backend**: Django 4.2+, Django REST Framework
- **Database**: PostgreSQL (production), SQLite (development)
- **AI**: OpenAI GPT-4/5
- **Maps**: Google Maps API
- **Authentication**: Django-allauth, OAuth2, JWT-ready
- **Caching**: Django cache framework
- **Testing**: pytest, Django TestCase
- **Frontend**: Modern responsive design

### Key Components
- **Models**: User, TripPlanRequest, GeneratedPlan, Destination
- **Services**: CostOptimizedGoogleMapsService, CostOptimizedOpenAIService
- **API**: RESTful endpoints with comprehensive serialization
- **Monitoring**: Real-time cost tracking and optimization

## 📚 Documentation

- **[Project Structure](PROJECT_STRUCTURE.md)** - Complete architecture overview
- **[Developer Onboarding](docs/development/DEVELOPER_ONBOARDING.md)** - Getting started guide
- **[API Documentation](docs/api/)** - Detailed API reference
- **[Deployment Guide](docs/deployment/)** - Production deployment
- **[Error Troubleshooting](docs/development/)** - Common issues and fixes

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes with tests**
4. **Follow code style**: PEP 8, comprehensive docstrings
5. **Submit pull request**

### Code Style Guidelines
- Follow PEP 8 for Python code
- Use Django conventions
- Write comprehensive docstrings
- Include type hints where appropriate
- Maintain test coverage above 85%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT API
- **Google** for Maps API and OAuth2
- **Django Community** for the excellent framework
- **DRF Team** for the REST framework

---

## 🔗 Quick Links

- [🏗️ Project Structure](PROJECT_STRUCTURE.md)
- [🚀 Developer Guide](docs/development/DEVELOPER_ONBOARDING.md)
- [🔐 JWT Migration](docs/development/DEVELOPER_ONBOARDING.md#jwt-migration)
- [🧪 Testing Guide](docs/development/DEVELOPER_ONBOARDING.md#testing-guidelines)
- [📊 API Reference](docs/api/)
- [🚀 Deployment](docs/deployment/DEPLOYMENT_CHECKLIST.md)

**Ready to build amazing travel experiences with AI?** 🌟

Start by examining the DRF API implementation in `home/api_views.py` and `home/serializers.py`!

# 🌍 TripAI - Intelligent Travel Planning Platform

> *Your AI-powered travel companion for creating personalized, professional trip itineraries with real-time location data and beautiful PDF reports.*

[![Django](https://img.shields.io/badge/Django-5.1.6-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenAI GPT-4](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com)
[![Google Maps](https://img.shields.io/badge/Google-Maps%20API-red.svg)](https://developers.google.com/maps)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Key Features

### 🤖 **Advanced AI Travel Assistant**
- **GPT-4 Turbo Integration**: Latest OpenAI model for intelligent travel recommendations
- **Multi-Modal Communication**: Text, voice, file uploads, and image analysis
- **Contextual Conversations**: Maintains chat history for personalized responses
- **Real-Time Processing**: Instant responses with typing indicators
- **Speech Recognition**: Browser-based voice-to-text input
- **File Analysis**: Upload documents, images, and audio for travel planning

### 🗺️ **Google Maps Integration**
- **Places API**: Real location data with photos, ratings, and details
- **Smart Location Extraction**: AI-powered location detection from itineraries
- **Interactive Maps**: Clickable links for every destination
- **Photo Collections**: Up to 3 high-quality photos per location
- **Autocomplete Search**: Intelligent destination suggestions
- **Geo-Coordinates**: Precise location mapping and directions

### 📄 **Professional PDF Generation**
- **ReportLab Engine**: High-quality PDF creation with custom styling
- **Embedded Media**: Location photos and maps integrated in documents
- **Interactive Elements**: Clickable Google Maps links
- **Emoji Support**: Modern, visually appealing formatting
- **Multi-Format Export**: PDF, text, and web-based viewing
- **Manual Regeneration**: On-demand PDF creation and updates

### 👥 **User Management & Profiles**
- **Secure Authentication**: Registration, login, and user sessions
- **Personalized Dashboards**: Individual trip history and preferences
- **Trip Collections**: Organized view of all travel plans
- **Support Tickets**: Integrated help system with chat context
- **Progress Tracking**: Real-time status updates for trip generation

### 🧳 **Intelligent Trip Planning**
- **AI-Powered Itineraries**: Customized plans based on budget, duration, and interests
- **Background Processing**: Non-blocking trip generation
- **Status Monitoring**: Real-time progress tracking with visual feedback
- **Fallback Systems**: Enhanced plans even when AI APIs are unavailable
- **Multiple Destinations**: Support for complex, multi-city travel plans
- **Budget Optimization**: Cost-effective recommendations within user constraints

### 🎨 **Modern User Interface**
- **Responsive Design**: Perfect on desktop, tablet, and mobile devices
- **Glass Morphism**: Modern UI with blur effects and gradients
- **Smooth Animations**: CSS transitions and micro-interactions
- **Loading States**: Visual feedback during processing
- **Interactive Cards**: Hover effects and dynamic content
- **Dark/Light Themes**: Consistent styling across all pages

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL (or change to SQLite for development)
- pip (Python package manager)
- **reportlab** (for PDF generation)

### Installation

1. **Clone the repository**:
   ```bash
   cd ~/Desktop/trip-django
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**:
   
   For PostgreSQL (current setup):
   - Create a PostgreSQL database named 'Hatef'
   - Update `main/settings.py` with your database credentials
   
   For SQLite (easier for development):
   - Change the DATABASES setting in `main/settings.py` to:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
       }
   }
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate sample destinations**:
   ```bash
   python manage.py populate_destinations
   ```

8. **Collect static files** (if needed):
   ```bash
   python manage.py collectstatic
   ```

9. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

10. **Access the application**:
    - Main site: http://127.0.0.1:8000/
    - Admin panel: http://127.0.0.1:8000/admin/
    - Chatbot: http://127.0.0.1:8000/chatbot/

## Usage

### Chatbot Features

1. **Text Chat**: Type messages and get AI responses about travel planning
2. **File Attachments**: Click the paperclip icon to attach travel documents, itineraries, etc.
3. **Image Attachments**: Click the image icon to attach photos
4. **Voice Recording**: Click the microphone icon to record voice messages
5. **Speech Recognition**: Click the microphone in the header to use speech-to-text
6. **Clear Chat**: Click the trash icon to clear chat history

### Browser Permissions

For voice features to work, you'll need to grant microphone permissions when prompted by your browser.

### Supported File Types

- **Images**: .jpg, .jpeg, .png, .gif
- **Documents**: .pdf, .doc, .docx, .txt, .csv, .xlsx
- **Audio**: .mp3, .wav, .ogg, .m4a

## GPT-4 Turbo Integration ✅

The chatbot is now fully integrated with **OpenAI GPT-4 Turbo** for intelligent travel assistance!

### Features:
- **GPT-4 Turbo**: Latest OpenAI model for superior responses
- **Vision Support**: Can analyze uploaded images and identify locations
- **Context Awareness**: Maintains conversation history for better responses
- **Specialized Prompts**: Optimized for travel planning and recommendations
- **Fallback System**: Graceful handling of API errors

### Configuration:
The AI service is configured in `home/services.py` with:
- Professional travel assistant prompts
- Image analysis capabilities
- Chat history context
- Error handling and fallbacks

Environment variables (see .env.example):
- OPENAI_MODEL (default: gpt-4-turbo)
- TEMPERATURE (default: 0.7 for optimal travel planning responses)
- MAX_TOKENS (used as max_tokens parameter for GPT-4 family)

### API Usage:
The system uses environment variables for secure API key management. All OpenAI interactions are handled through the `AIService` class.

## Production Deployment

Before deploying to production:

1. Set `DEBUG = False` in settings.py
2. Use environment variables for sensitive data (database credentials, secret keys)
3. Configure proper static file serving
4. Set up HTTPS
5. Configure allowed hosts
6. Use a production database
7. Set up proper logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational/prototype purposes. Please add your own license as needed.

## Support

For issues or questions, please create an issue in the repository or contact the development team.
