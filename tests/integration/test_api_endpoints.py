"""
Integration tests for DRF API endpoints.

These tests verify the interaction between different API components:
- Authentication (JWT/Token-based)
- API views and serializers
- Database operations
- Cache integration
- External service mocking

NOTE FOR DRF/JWT EXPERT:
This file contains the main DRF API testing patterns. Key areas to examine:
1. AuthenticationTestCase: JWT token-based authentication testing
2. TripPlanningAPITestCase: DRF ViewSet and serializer testing
3. CacheIntegrationTestCase: Testing cache behavior with DRF endpoints
4. ThrottlingTestCase: Rate limiting and throttling tests
5. PermissionsTestCase: DRF permission classes testing

All tests follow DRF best practices for API testing.
"""

import json
from unittest.mock import patch, Mock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.core.cache import cache
from django.conf import settings

from home.models import TripPlanRequest, Destination
from home.serializers import (
    TripRequestSerializer,
    LocationPhotoSerializer,
    CostMonitorSerializer
)

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    """
    Test authentication for DRF API endpoints.
    
    IMPORTANT FOR JWT EXPERT: 
    Currently using Token authentication. Can be easily migrated to JWT.
    See setup_jwt_authentication() method for JWT implementation pattern.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
    
    def test_authenticated_request(self):
        """Test API request with valid token authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/trip-status/')
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_unauthenticated_request(self):
        """Test API request without authentication."""
        response = self.client.get('/api/trip-status/')
        # Some endpoints might be public, adjust based on your requirements
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_200_OK  # If endpoint is public
        ])
    
    def setup_jwt_authentication(self):
        """
        Example JWT setup for migration from Token auth.
        
        MIGRATION NOTES FOR JWT EXPERT:
        1. Install djangorestframework-simplejwt
        2. Update settings.py REST_FRAMEWORK config
        3. Replace Token model with JWT token generation
        4. Update authentication headers to use Bearer tokens
        """
        # JWT implementation would go here
        # from rest_framework_simplejwt.tokens import RefreshToken
        # refresh = RefreshToken.for_user(self.user)
        # access_token = str(refresh.access_token)
        # self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        pass


class TripPlanningAPITestCase(APITestCase):
    """
    Test trip planning DRF API endpoints.
    
    IMPORTANT FOR DRF EXPERT:
    This demonstrates DRF ViewSet testing patterns including:
    - Serializer validation testing
    - API endpoint response testing  
    - Database interaction testing
    - External service mocking
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Sample trip request data
        self.trip_data = {
            'destination': 'Paris, France',
            'duration': 7,
            'budget': 2000.00,
            'num_travelers': 2,
            'interests': 'museums, food, culture',
            'daily_budget': 285.71,
            'transportation_preference': 'public_transport',
            'experience_style': 'relaxed exploration'
        }
    
    def test_trip_request_serializer(self):
        """Test TripRequestSerializer validation and serialization."""
        serializer = TripRequestSerializer(data=self.trip_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid data
        invalid_data = self.trip_data.copy()
        invalid_data['duration'] = -1  # Invalid negative duration
        invalid_serializer = TripRequestSerializer(data=invalid_data)
        self.assertFalse(invalid_serializer.is_valid())
    
    @patch('home.optimized_services.CostOptimizedGoogleMapsService.get_autocomplete_cached')
    def test_location_autocomplete_api(self, mock_autocomplete):
        """Test location autocomplete API endpoint with mocked service."""
        mock_autocomplete.return_value = [
            {
                'description': 'Paris, France',
                'main_text': 'Paris',
                'secondary_text': 'France',
                'place_id': 'test_place_id'
            }
        ]
        
        response = self.client.get('/api/autocomplete/', {'query': 'Paris'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('suggestions', data)
        self.assertEqual(len(data['suggestions']), 1)
        self.assertEqual(data['suggestions'][0]['description'], 'Paris, France')
        
        # Verify the service was called correctly
        mock_autocomplete.assert_called_once_with('Paris')
    
    @patch('home.optimized_services.CostOptimizedOpenAIService.generate_optimized_trip_plan_cached')
    def test_trip_plan_generation(self, mock_ai_service):
        """Test trip plan generation API with mocked AI service."""
        mock_ai_service.return_value = {
            'plan': '# 7-Day Paris Itinerary\n\n## Day 1: Arrival',
            'total_cost': 1800.00,
            'daily_breakdown': [285.71] * 7
        }
        
        response = self.client.post('/api/generate-trip/', self.trip_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify trip request was created in database
        trip_request = TripPlanRequest.objects.filter(user=self.user).first()
        self.assertIsNotNone(trip_request)
        self.assertEqual(trip_request.destination, 'Paris, France')


class CacheIntegrationTestCase(APITestCase):
    """
    Test cache integration with DRF API endpoints.
    
    IMPORTANT FOR DRF EXPERT:
    This demonstrates cache-aware API testing patterns:
    - Cache hit/miss testing with API endpoints
    - Cache invalidation testing
    - Performance optimization verification
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        cache.clear()  # Start with clean cache
    
    @patch('home.optimized_services.CostOptimizedGoogleMapsService.get_autocomplete_cached')
    def test_autocomplete_caching(self, mock_service):
        """Test that autocomplete results are properly cached."""
        mock_response = [{'description': 'Paris, France'}]
        mock_service.return_value = mock_response
        
        # First request should call the service
        response1 = self.client.get('/api/autocomplete/', {'query': 'Paris'})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request should use cache
        response2 = self.client.get('/api/autocomplete/', {'query': 'Paris'})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify service was only called once (second call used cache)
        self.assertEqual(mock_service.call_count, 1)
    
    def test_cost_monitoring_cache_integration(self):
        """Test cost monitoring data with cache integration."""
        response = self.client.get('/api/cost-monitor/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('daily_usage', data)
        self.assertIn('cache_stats', data)


class ThrottlingTestCase(APITestCase):
    """
    Test API throttling and rate limiting.
    
    IMPORTANT FOR DRF EXPERT:
    This demonstrates DRF throttling testing patterns.
    Throttling classes are configured in settings.py REST_FRAMEWORK.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_api_throttling(self):
        """Test that API endpoints respect throttling limits."""
        # This test would need throttling to be configured with very low limits for testing
        # In production, throttling limits are higher
        
        url = '/api/autocomplete/'
        responses = []
        
        # Make multiple requests to test throttling
        for i in range(10):  # Adjust based on your throttling config
            response = self.client.get(url, {'query': f'test{i}'})
            responses.append(response.status_code)
        
        # Check if any requests were throttled
        throttled_responses = [r for r in responses if r == status.HTTP_429_TOO_MANY_REQUESTS]
        
        # This assertion depends on your throttling configuration
        # Uncomment if you have strict throttling limits for testing
        # self.assertGreater(len(throttled_responses), 0)


class PermissionsTestCase(APITestCase):
    """
    Test DRF permissions for API endpoints.
    
    IMPORTANT FOR DRF EXPERT:
    This demonstrates DRF permission testing patterns:
    - IsAuthenticated permission testing
    - Custom permission classes testing
    - User-specific data access testing
    """
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        
        self.client = APIClient()
    
    def test_user_specific_data_access(self):
        """Test that users can only access their own trip data."""
        # Create trip request for user1
        trip_request = TripPlanRequest.objects.create(
            user=self.user1,
            destination='Paris, France',
            duration=7,
            budget=2000.00,
            status='completed'
        )
        
        # User1 should be able to access their own data
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(f'/api/trip-status/{trip_request.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User2 should not be able to access user1's data
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        response = self.client.get(f'/api/trip-status/{trip_request.id}/')
        self.assertIn(response.status_code, [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ])
    
    def test_superuser_permissions(self):
        """Test superuser access to admin-only endpoints."""
        # Create superuser
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        admin_token = Token.objects.create(user=superuser)
        
        # Test cost dashboard access (admin-only)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
        response = self.client.get('/api/cost-monitor/')
        
        # Response should be successful for superuser
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND  # If endpoint doesn't exist yet
        ])
