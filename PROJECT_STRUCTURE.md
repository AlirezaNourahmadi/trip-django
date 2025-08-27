# TripAI Project Structure

## 📋 Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Architecture Overview](#architecture-overview)
- [API Documentation](#api-documentation)
- [For DRF/JWT Experts](#for-drfjwt-experts)
- [Development Guidelines](#development-guidelines)
- [Testing Strategy](#testing-strategy)
- [Deployment](#deployment)

## 🎯 Overview

TripAI is a Django web application that generates personalized travel itineraries using AI (OpenAI GPT) and Google Maps APIs. The application features cost optimization, intelligent caching, and a modern REST API built with Django REST Framework.

### Key Features
- ✈️ AI-powered trip planning with GPT-4/5
- 🗺️ Google Maps integration for locations and photos
- 💰 Cost optimization and monitoring
- 📄 PDF generation for trip itineraries
- 🔒 OAuth2 authentication with Google
- 📊 Real-time cost dashboard
- 🚀 RESTful API with DRF

## 📁 Directory Structure

```
trip-django/
├── 📁 apps/                          # Future: Modular app structure
│   ├── api/                          # API-specific modules
│   ├── authentication/               # Auth-related modules  
│   ├── core/                        # Core business logic
│   └── trip_planning/               # Trip planning modules
├── 📁 docs/                         # Documentation
│   ├── api/                         # API documentation
│   ├── deployment/                  # Deployment guides
│   └── development/                 # Development docs
├── 📁 home/                         # Main Django app
│   ├── 📄 adapters.py              # Social auth adapters
│   ├── 📄 admin.py                 # Django admin config
│   ├── 📄 api_views.py             # 🔥 DRF API views
│   ├── 📄 apps.py                  # App configuration
│   ├── 📄 cost_monitor.py          # Cost tracking service
│   ├── 📄 forms.py                 # Django forms
│   ├── 📄 models.py                # Database models
│   ├── 📄 optimized_services.py    # 🔥 Optimized external APIs
│   ├── 📄 serializers.py           # 🔥 DRF serializers
│   ├── 📄 services.py              # Legacy services
│   ├── 📄 signals.py               # Django signals
│   ├── 📄 urls.py                  # URL routing
│   ├── 📄 views.py                 # Django views
│   ├── 📁 management/              # Custom management commands
│   │   └── commands/
│   │       ├── populate_destinations.py
│   │       ├── regenerate_pdf.py
│   │       ├── setup_google_oauth.py
│   │       └── test_google_oauth.py
│   ├── 📁 migrations/              # Database migrations
│   ├── 📁 templates/               # Legacy templates
│   └── 📁 templatetags/            # Custom template tags
├── 📁 logs/                        # Application logs
├── 📁 main/                        # Django project settings
│   ├── 📄 settings.py              # 🔥 Main configuration
│   ├── 📄 urls.py                  # Root URL routing
│   ├── 📄 wsgi.py                  # WSGI config
│   └── 📄 asgi.py                  # ASGI config
├── 📁 scripts/                     # Utility scripts
│   ├── deployment/                 # Deployment scripts
│   ├── development/                # Development utilities
│   └── maintenance/                # Maintenance scripts
├── 📁 static/                      # Static files (global)
│   ├── css/                        # Stylesheets
│   ├── js/                         # JavaScript files
│   ├── img/                        # Images
│   └── fonts/                      # Font files
├── 📁 templates/                   # Templates (global)
│   ├── base/                       # Base templates
│   ├── auth/                       # Authentication templates
│   ├── errors/                     # Error pages
│   ├── home/                       # Home app templates
│   ├── legal/                      # Legal pages
│   └── components/                 # Reusable components
└── 📁 tests/                       # 🔥 Comprehensive tests
    ├── functional/                 # End-to-end tests
    ├── integration/                # API integration tests
    ├── unit/                       # Unit tests
    ├── 📄 conftest.py             # Pytest configuration
    └── 📄 test_runner.py          # Custom test runner

🔥 = Critical files for DRF/JWT experts
```

## 🏗️ Architecture Overview

### Django Apps Structure

#### Current Structure (Single App)
- **home/**: Main application containing all business logic

#### Future Structure (Modular)
- **apps/core/**: Shared utilities and base classes
- **apps/authentication/**: User management and auth
- **apps/trip_planning/**: Trip planning business logic
- **apps/api/**: API-specific logic and versioning

### Key Components

#### 1. Models (`home/models.py`)
- **User**: Custom user model with OAuth integration
- **TripPlanRequest**: Trip request data and preferences
- **GeneratedPlan**: AI-generated trip plans with PDF files
- **Destination**: Location data cache

#### 2. API Layer (`home/api_views.py` & `home/serializers.py`)
- RESTful API built with Django REST Framework
- Token-based authentication (JWT-ready)
- Comprehensive input validation
- Intelligent caching and throttling

#### 3. Services Layer
- **`optimized_services.py`**: Cost-optimized external API integrations
- **`cost_monitor.py`**: Real-time cost tracking and monitoring
- **Legacy `services.py`**: Original implementation (to be refactored)

#### 4. External Integrations
- **OpenAI GPT-4/5**: AI trip planning
- **Google Maps API**: Location data and photos
- **Google OAuth2**: User authentication

## 🔌 API Documentation

### Base URLs
- **Development**: `http://127.0.0.1:8000/api/`
- **Production**: `https://your-domain.com/api/`

### Authentication
```http
# Token Authentication (Current)
Authorization: Token <your-token>

# JWT Authentication (Future)
Authorization: Bearer <jwt-token>
```

### Core Endpoints

#### Trip Management
```http
GET    /api/trip-status/<int:trip_id>/     # Check trip generation status
POST   /api/generate-pdf/<int:trip_id>/    # Generate PDF for trip
```

#### Location Services
```http
GET    /api/autocomplete/?query=<location>       # Location autocomplete
GET    /api/location-photos/?location=<name>     # Location photos
```

#### Admin (Superuser Only)
```http
GET    /api/cost-monitor/                  # Cost monitoring dashboard
```

### Response Formats

#### Success Response
```json
{
    "status": "success",
    "data": {
        "trip_id": 123,
        "status": "completed"
    }
}
```

#### Error Response
```json
{
    "status": "error",
    "message": "Trip not found",
    "code": "TRIP_NOT_FOUND"
}
```

## 🔥 For DRF/JWT Experts

### 🎯 Key Files to Examine

1. **`home/api_views.py`** - Main DRF API implementation
2. **`home/serializers.py`** - Comprehensive serializers with JWT patterns
3. **`main/settings.py`** - DRF and JWT configuration
4. **`tests/integration/test_api_endpoints.py`** - API testing patterns

### 🔐 JWT Migration Guide

The project is **JWT-ready**. To migrate from Token to JWT authentication:

#### 1. Install JWT Package
```bash
pip install djangorestframework-simplejwt
```

#### 2. Update Settings (`main/settings.py`)
```python
# Uncomment these lines in settings.py:
INSTALLED_APPS += ['rest_framework_simplejwt']

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]

# Configure JWT settings (already prepared in settings.py)
```

#### 3. Update URL Configuration
```python
# main/urls.py
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]
```

#### 4. Update Frontend Authentication
```javascript
// Change from:
headers: { 'Authorization': 'Token ' + token }

// To:
headers: { 'Authorization': 'Bearer ' + accessToken }
```

### 🏗️ DRF Architecture Patterns

#### ViewSets vs APIViews
- **Current**: Using `APIView` for specific endpoints
- **Recommendation**: Migrate to `ViewSets` for CRUD operations

#### Serializer Patterns
- **Validation**: Field-level and object-level validation
- **Context**: User context passing for JWT claims
- **Nested**: Complex data structures with nested serializers
- **Dynamic**: Context-dependent field inclusion

#### Permissions
```python
# Custom permission classes
class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_superuser
```

#### Throttling
```python
# Custom throttle classes
class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'
    
class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'
```

### 🔧 Advanced Features

#### 1. API Versioning
```python
# URL versioning pattern
path('api/v1/', include('home.api.v1.urls')),
path('api/v2/', include('home.api.v2.urls')),
```

#### 2. Custom Pagination
```python
class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

#### 3. Custom Renderers
```python
class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Custom response formatting
        return super().render(data, accepted_media_type, renderer_context)
```

## 📋 Development Guidelines

### Code Style
- **Python**: PEP 8 compliance
- **Django**: Django coding style
- **API**: RESTful principles
- **Documentation**: Comprehensive docstrings

### Git Workflow
```bash
# Feature branch workflow
git checkout -b feature/new-api-endpoint
git commit -m "feat: add trip sharing API endpoint"
git push origin feature/new-api-endpoint
# Create pull request
```

### Environment Setup
```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env with your API keys

# Database
python manage.py migrate
python manage.py createsuperuser
```

## 🧪 Testing Strategy

### Test Organization
- **Unit Tests**: `tests/unit/` - Test individual functions
- **Integration Tests**: `tests/integration/` - Test API endpoints
- **Functional Tests**: `tests/functional/` - Test user workflows

### Running Tests
```bash
# All tests
python manage.py test

# Specific test types
python tests/test_runner.py unit
python tests/test_runner.py integration
python tests/test_runner.py functional
python tests/test_runner.py api

# With coverage
pytest tests/ --cov=home --cov-report=html
```

### Test Patterns
```python
# API testing with DRF
class TripAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test')
        self.client.force_authenticate(user=self.user)
    
    def test_create_trip(self):
        response = self.client.post('/api/trips/', data)
        self.assertEqual(response.status_code, 201)
```

## 🚀 Deployment

### Environment Configuration

#### Development
```python
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
DATABASE = 'sqlite3' or 'postgresql'
```

#### Production
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
DATABASE = 'postgresql'
STATIC_ROOT = '/var/www/static/'
MEDIA_ROOT = '/var/www/media/'
```

### Required Environment Variables
```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False

# Database
DB_NAME=tripai_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# APIs
OPENAI_API_KEY=your-openai-key
GOOGLE_MAPS_API_KEY=your-google-maps-key

# OAuth
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
```

### Docker Deployment (Future)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "main.wsgi:application"]
```

## 📚 Additional Resources

### Documentation Files
- **`docs/deployment/`**: Deployment guides and checklists
- **`docs/development/`**: Development troubleshooting
- **`docs/api/`**: Detailed API documentation

### Management Commands
```bash
python manage.py populate_destinations    # Populate location data
python manage.py regenerate_pdf <trip_id> # Regenerate trip PDF
python manage.py setup_google_oauth       # Configure OAuth
```

### Monitoring and Logging
- **Cost Dashboard**: Real-time API cost monitoring
- **Django Logs**: Structured logging with levels
- **Error Tracking**: Comprehensive error handling

---

## 🤝 Contributing

For developers wanting to contribute, especially DRF/JWT experts:

1. **Fork the repository**
2. **Set up development environment**
3. **Examine the key DRF files** (marked with 🔥)
4. **Run tests** to understand current functionality
5. **Review API documentation** and test endpoints
6. **Submit pull requests** with comprehensive tests

### Quick Start for DRF Experts

```bash
# 1. Clone and setup
git clone <repo-url>
cd trip-django
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Environment setup
cp .env.example .env
# Add your API keys to .env

# 3. Database setup
python manage.py migrate
python manage.py createsuperuser

# 4. Run tests
python tests/test_runner.py api

# 5. Start development server
python manage.py runserver

# 6. Test API endpoints
curl -H "Authorization: Token <your-token>" \
     http://127.0.0.1:8000/api/trip-status/1/
```

The project is well-structured for immediate DRF development and ready for JWT migration. Focus on the files marked with 🔥 for the core API implementation.
