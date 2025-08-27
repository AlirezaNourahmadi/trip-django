# 🚀 Developer Onboarding Guide

Welcome to TripAI! This guide will get you up and running quickly, with special attention to Django REST Framework (DRF) and JWT experts.

## 📋 Quick Navigation

- [🔥 For DRF/JWT Experts (Skip to This)](#-for-drfjwt-experts)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Project Architecture](#project-architecture)
- [API Development](#api-development)
- [Testing Guidelines](#testing-guidelines)
- [Common Tasks](#common-tasks)

## 🔥 For DRF/JWT Experts

### TL;DR - Get Started in 5 Minutes

```bash
# 1. Clone and setup environment
git clone <repo-url> && cd trip-django
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Quick environment setup
cp .env.example .env
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "GOOGLE_MAPS_API_KEY=your_key_here" >> .env

# 3. Database setup
python manage.py migrate
python manage.py createsuperuser

# 4. Run API tests to understand the system
python tests/test_runner.py api

# 5. Start development
python manage.py runserver
```

### 🎯 Key Files to Examine First

| Priority | File | Purpose |
|----------|------|---------|
| 🔥 **HIGH** | `home/api_views.py` | Main DRF API views with auth patterns |
| 🔥 **HIGH** | `home/serializers.py` | Complete DRF serializers with JWT patterns |
| 🔥 **HIGH** | `main/settings.py` | DRF/JWT configuration |
| 🔥 **HIGH** | `tests/integration/test_api_endpoints.py` | API testing patterns |
| **MEDIUM** | `home/models.py` | Data models and relationships |
| **MEDIUM** | `home/optimized_services.py` | External API integrations |
| **LOW** | `home/views.py` | Legacy Django views |

### 🔐 JWT Migration Status

✅ **Ready for JWT** - The project is fully prepared for JWT migration:

- JWT configuration prepared in `settings.py` (just uncomment)
- Serializers include JWT context patterns
- API views designed for JWT authentication
- Test patterns include JWT authentication examples

**To enable JWT** (2-minute setup):
```python
# 1. Install package
pip install djangorestframework-simplejwt

# 2. Uncomment JWT lines in main/settings.py
# Lines 232-234 and 261-273

# 3. Update API authentication headers
# From: Authorization: Token <token>
# To: Authorization: Bearer <jwt-token>
```

### 🏗️ API Architecture Overview

```
Current API Structure:
├── Authentication: Token-based (JWT-ready)
├── Throttling: User/Anonymous rate limiting
├── Caching: Intelligent cache with TTL
├── Validation: Comprehensive serializers
└── Testing: Full API test coverage

Key API Endpoints:
├── /api/trip-status/<id>/       (GET) - Trip status
├── /api/generate-pdf/<id>/      (POST) - Generate PDF
├── /api/autocomplete/           (GET) - Location search
├── /api/location-photos/        (GET) - Photos
└── /api/cost-monitor/           (GET) - Admin only
```

### 🎯 Development Focus Areas

#### Immediate Opportunities:
1. **JWT Migration**: Enable JWT authentication
2. **ViewSets**: Convert APIViews to ViewSets for CRUD
3. **API Versioning**: Add v1/v2 API versioning
4. **Permissions**: Enhance custom permission classes
5. **Pagination**: Implement advanced pagination

#### Advanced Features:
1. **WebSocket Support**: Real-time trip status updates
2. **GraphQL Layer**: GraphQL API alongside REST
3. **API Throttling**: Advanced throttling strategies
4. **Caching**: Redis caching implementation
5. **Monitoring**: API metrics and monitoring

---

## 📋 Prerequisites

### Required Knowledge
- **Python 3.9+**: Modern Python features
- **Django 4.2+**: Latest Django LTS
- **Django REST Framework**: API development
- **PostgreSQL**: Database operations
- **Git**: Version control

### Optional but Helpful
- **JWT/Token Auth**: Authentication patterns
- **Redis**: Caching implementation
- **Docker**: Containerization
- **OpenAI API**: AI integration understanding
- **Google Maps API**: Location services

## 🛠️ Environment Setup

### 1. System Requirements

```bash
# Python version
python --version  # Should be 3.9+

# PostgreSQL (optional - SQLite works for development)
psql --version

# Git
git --version
```

### 2. Project Setup

```bash
# Clone repository
git clone <repository-url>
cd trip-django

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Create `.env` file from template:
```bash
cp .env.example .env
```

Configure required variables:
```bash
# .env file
DJANGO_SECRET_KEY=your-django-secret-key
DEBUG=True

# Database (optional for development)
DB_NAME=tripai_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Required API Keys
OPENAI_API_KEY=your-openai-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# OAuth (optional)
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret

# OpenAI Model Configuration
OPENAI_MODEL=gpt-4o  # or gpt-5 for latest
TEMPERATURE=1.0
MAX_TOKENS=4000
```

### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Optional: Populate sample data
python manage.py populate_destinations
```

### 5. Verify Setup

```bash
# Run tests
python manage.py test

# Start development server
python manage.py runserver

# Test API endpoint
curl http://127.0.0.1:8000/api/autocomplete/?query=Paris
```

## 🏗️ Project Architecture

### Directory Structure

```
📁 Key Directories for API Development:
├── home/api_views.py         # 🔥 Main API endpoints
├── home/serializers.py       # 🔥 Data validation/serialization
├── home/models.py           # Database models
├── tests/integration/       # 🔥 API tests
├── main/settings.py         # 🔥 DRF configuration
└── docs/                    # Documentation
```

### Data Models

```python
# Key models for API development:
User                # Custom user model with OAuth
├── TripPlanRequest  # Trip parameters and preferences
    └── GeneratedPlan # AI-generated content and PDFs
Destination         # Cached location data
```

### Service Layer

```python
# External API integrations:
CostOptimizedGoogleMapsService  # Google Maps with caching
CostOptimizedOpenAIService      # OpenAI with cost monitoring
CostMonitor                     # Real-time cost tracking
```

## 🔌 API Development

### Current API Endpoints

```http
# Trip Management
GET    /api/trip-status/<int:trip_id>/
POST   /api/generate-pdf/<int:trip_id>/

# Location Services  
GET    /api/autocomplete/?query=<location>
GET    /api/location-photos/?location=<name>&destination=<city>

# Admin Only
GET    /api/cost-monitor/
```

### Authentication Patterns

```python
# Current: Token Authentication
class MyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        token = request.auth
        # Your logic here

# JWT Pattern (ready to implement):
class MyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # JWT payload available through user context
        # jwt_payload = getattr(user, 'jwt_payload', {})
```

### Serializer Patterns

```python
# Field validation
def validate_field_name(self, value):
    if some_condition:
        raise serializers.ValidationError("Error message")
    return value

# Object validation
def validate(self, data):
    if data['field1'] and data['field2']:
        # Cross-field validation
        pass
    return data

# Custom representation
def to_representation(self, instance):
    data = super().to_representation(instance)
    # Modify data based on user context
    return data
```

### Testing Patterns

```python
# API testing with authentication
class APITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_endpoint(self):
        response = self.client.get('/api/endpoint/')
        self.assertEqual(response.status_code, 200)
```

## 🧪 Testing Guidelines

### Test Organization

```bash
tests/
├── unit/              # Individual function tests
├── integration/       # API endpoint tests
├── functional/        # End-to-end workflows
├── conftest.py        # Pytest configuration
└── test_runner.py     # Custom test runner
```

### Running Tests

```bash
# All tests
python manage.py test

# Specific categories
python tests/test_runner.py unit
python tests/test_runner.py integration
python tests/test_runner.py api

# With coverage
pytest --cov=home --cov-report=html
```

### Test Coverage Goals
- **API Endpoints**: 100% coverage
- **Serializers**: 95% coverage
- **Models**: 90% coverage
- **Services**: 85% coverage

## 🔧 Common Tasks

### Adding New API Endpoint

1. **Create serializer** in `home/serializers.py`
2. **Add API view** in `home/api_views.py`
3. **Update URLs** in `home/urls.py`
4. **Write tests** in `tests/integration/`
5. **Document endpoint** in API docs

### JWT Implementation

```python
# 1. Install package
pip install djangorestframework-simplejwt

# 2. Update settings.py
INSTALLED_APPS += ['rest_framework_simplejwt']

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
]

# 3. Add JWT URLs
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]
```

### Adding Custom Permissions

```python
from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in SAFE_METHODS:
            return True
        # Write permissions only for owners
        return obj.user == request.user
```

### Caching Implementation

```python
from django.core.cache import cache

class CachedAPIView(APIView):
    def get(self, request):
        cache_key = f"api_data_{request.user.id}"
        data = cache.get(cache_key)
        
        if not data:
            # Generate data
            data = expensive_operation()
            cache.set(cache_key, data, 3600)  # Cache for 1 hour
            
        return Response(data)
```

## 📊 Performance Optimization

### Database Optimization

```python
# Use select_related for ForeignKey
queryset = Model.objects.select_related('foreign_key')

# Use prefetch_related for ManyToMany
queryset = Model.objects.prefetch_related('many_to_many_field')

# Optimize serializers
class OptimizedSerializer(ModelSerializer):
    class Meta:
        model = MyModel
        fields = ['essential_field_1', 'essential_field_2']  # Only needed fields
```

### API Response Optimization

```python
# Pagination for large datasets
class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# Custom renderers for specific formats
class OptimizedJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Custom optimizations
        return super().render(data, accepted_media_type, renderer_context)
```

## 🐛 Debugging Tips

### Common Issues

1. **Authentication Errors**
   ```bash
   # Check token validity
   python manage.py shell
   >>> from rest_framework.authtoken.models import Token
   >>> Token.objects.filter(user__username='your_username')
   ```

2. **Database Migration Issues**
   ```bash
   # Reset migrations (development only)
   python manage.py migrate --fake home zero
   rm home/migrations/000*.py
   python manage.py makemigrations home
   python manage.py migrate
   ```

3. **API Endpoint Not Found**
   ```bash
   # Check URL patterns
   python manage.py show_urls | grep api
   ```

### Logging

```python
# Enable debug logging
import logging
logger = logging.getLogger(__name__)

def my_view(request):
    logger.debug(f"Request data: {request.data}")
    logger.info(f"Processing request for user: {request.user}")
```

## 📚 Additional Resources

### Documentation Links
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Project Structure Documentation](../PROJECT_STRUCTURE.md)

### Internal Documentation
- `docs/api/` - Detailed API documentation  
- `docs/deployment/` - Deployment guides
- `docs/development/` - Development troubleshooting

### Management Commands
```bash
# Useful development commands
python manage.py shell_plus        # Enhanced Django shell
python manage.py show_urls          # List all URL patterns
python manage.py makemigrations     # Create new migrations
python manage.py migrate           # Apply migrations
python manage.py collectstatic     # Collect static files
```

## 🤝 Contributing

### Pull Request Process
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open pull request

### Code Style
- Follow PEP 8 for Python code
- Use Django coding conventions
- Write comprehensive docstrings
- Include type hints where appropriate

### Testing Requirements
- All new API endpoints must have tests
- Maintain test coverage above 85%
- Include both positive and negative test cases
- Test authentication and permissions

---

## 🚀 Ready to Start?

You're all set! Here's your development workflow:

1. **Start with the API** - Examine `home/api_views.py` and `home/serializers.py`
2. **Run the tests** - Understand current functionality
3. **Make a small change** - Add a simple API endpoint
4. **Test thoroughly** - Write comprehensive tests
5. **Submit PR** - Follow the contribution guidelines

**Need help?** Check the documentation or create an issue!

Happy coding! 🎉
