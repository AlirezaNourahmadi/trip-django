"""
Test configuration for TripAI Django project.

This file contains shared fixtures and configurations for all test types:
- Unit tests: Test individual functions and methods in isolation
- Integration tests: Test interaction between components
- Functional tests: Test end-to-end user workflows

Pytest fixtures defined here are available to all test modules.
"""

import os
import sys
import django
import pytest
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line


# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def pytest_configure():
    """Configure Django settings for pytest."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
    django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up database for tests."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }


@pytest.fixture
def api_client():
    """DRF API test client fixture."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(django_user_model):
    """Authenticated DRF API client fixture."""
    from rest_framework.test import APIClient
    from rest_framework.authtoken.models import Token
    
    client = APIClient()
    user = django_user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    token, created = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    client.user = user
    return client


@pytest.fixture
def sample_trip_request():
    """Sample trip request data for testing."""
    return {
        'destination': 'Paris, France',
        'duration': 7,
        'budget': 2000.00,
        'num_travelers': 2,
        'interests': 'museums, food, culture',
        'daily_budget': 285.71,
        'transportation_preference': 'public_transport',
        'experience_style': 'relaxed exploration'
    }


@pytest.fixture
def mock_google_places_response():
    """Mock Google Places API response."""
    return {
        'predictions': [
            {
                'description': 'Paris, France',
                'structured_formatting': {
                    'main_text': 'Paris',
                    'secondary_text': 'France'
                },
                'place_id': 'ChIJD7fiBh9u5kcRYJSMaMOCCwQ'
            }
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        'choices': [
            {
                'message': {
                    'content': '''# 7-Day Paris Itinerary 🇫🇷

## Day 1: Arrival & Exploration
- **Morning**: Arrive in Paris, check into accommodation
- **Afternoon**: Visit Notre-Dame Cathedral area
- **Evening**: Seine River walk

**Estimated Daily Cost**: $285
                    '''
                }
            }
        ]
    }
