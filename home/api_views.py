"""
DRF API Views for TripAI Application

This module contains all Django REST Framework API endpoints for the TripAI application.
All views follow DRF best practices with proper authentication, throttling, and caching.

NOTE FOR DRF/JWT EXPERT:
=====================
This file contains the main DRF API implementation. Key architectural decisions:

1. AUTHENTICATION:
   - Currently using Token Authentication (can migrate to JWT)
   - Permission classes configured per view for granular access control
   - Ready for JWT migration (see settings.py for JWT configuration)

2. THROTTLING:
   - UserRateThrottle for authenticated requests
   - AnonRateThrottle for anonymous requests (configured in settings)
   - Custom throttle rates per API endpoint

3. CACHING STRATEGY:
   - Django cache framework integration
   - Cache keys with intelligent naming
   - TTL (Time To Live) optimized per endpoint type

4. SERIALIZATION:
   - Input validation using DRF serializers
   - Response data validation
   - Custom field validation and error handling

5. ERROR HANDLING:
   - Structured error responses
   - Logging integration for debugging
   - HTTP status codes following REST conventions

MIGRATION TO JWT:
================
To migrate to JWT authentication:
1. Install djangorestframework-simplejwt
2. Update settings.py (JWT configuration already prepared)
3. Replace TokenAuthentication with JWTAuthentication in DEFAULT_AUTHENTICATION_CLASSES
4. Update client-side to use Bearer tokens instead of Token auth
5. Implement JWT refresh token handling

API VERSIONING:
==============
For API versioning, consider:
- URL path versioning: /api/v1/endpoint/
- Header-based versioning: Accept: application/vnd.api+json; version=1.0
- Parameter-based versioning: ?version=1.0
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings
import logging
import json

# Import models and serializers
from .models import TripPlanRequest, GeneratedPlan
from .serializers import (
    LocationDetailsSerializer, AutocompleteResponseSerializer,
    TripStatusSerializer, PDFGenerationSerializer,
    CostUsageSerializer, CostRecommendationSerializer  # Additional serializers
)

# Configure logger for this module
logger = logging.getLogger(__name__)


class LocationPhotosAPIView(APIView):
    """
    Optimized API endpoint for fetching location photos from Google Places
    with intelligent caching to reduce API costs
    """
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        location_name = request.GET.get('location', '').strip()
        destination_city = request.GET.get('destination', '').strip()
        
        if not location_name:
            return Response(
                {'error': 'Location name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create cache key for this location query
        cache_key = f"location_photos_{location_name}_{destination_city}".lower().replace(' ', '_')
        
        # Try to get cached result first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"✅ Cache hit for location photos: {location_name}")
            return Response(cached_data)
        
        try:
            # Use optimized Google Maps service with cost monitoring
            from .optimized_services import CostOptimizedGoogleMapsService
            
            gmaps_service = CostOptimizedGoogleMapsService()
            place_details = gmaps_service.get_place_details_cached(location_name, destination_city)
            
            if not place_details:
                response_data = {
                    'location': location_name,
                    'photos': [],
                    'rating': None,
                    'formatted_address': None,
                    'message': 'Location not found'
                }
            else:
                response_data = {
                    'location': location_name,
                    'place_id': place_details.get('place_id'),
                    'name': place_details.get('name'),
                    'photos': place_details.get('photos', []),
                    'rating': place_details.get('rating'),
                    'formatted_address': place_details.get('formatted_address'),
                    'types': place_details.get('types', []),
                    'maps_link': f"https://maps.google.com/?q=place_id:{place_details.get('place_id')}" if place_details.get('place_id') else None
                }
            
            # Cache the result for 6 hours to reduce API calls
            cache.set(cache_key, response_data, 6 * 60 * 60)
            logger.info(f"✅ Cached location photos for: {location_name}")
            
            # Validate response with serializer
            serializer = LocationDetailsSerializer(data=response_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response(response_data)  # Return raw data if validation fails
            
        except Exception as e:
            logger.error(f"Error getting location photos for {location_name}: {e}")
            return Response({
                'error': 'Failed to fetch location photos',
                'location': location_name,
                'photos': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlacesAutocompleteAPIView(APIView):
    """
    Optimized API endpoint for Google Places autocomplete with caching
    """
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        query = request.GET.get('query', '').strip()
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        # Create cache key for this autocomplete query
        cache_key = f"autocomplete_{query}".lower().replace(' ', '_')
        
        # Try to get cached result first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"✅ Cache hit for autocomplete: {query}")
            return Response(cached_data)
        
        try:
            # Use optimized Google Maps service
            from .optimized_services import CostOptimizedGoogleMapsService
            
            gmaps_service = CostOptimizedGoogleMapsService()
            suggestions = gmaps_service.get_autocomplete_cached(query)
            
            response_data = {'suggestions': suggestions}
            
            # Cache autocomplete results for 1 hour
            cache.set(cache_key, response_data, 60 * 60)
            logger.info(f"✅ Cached autocomplete results for: {query}")
            
            # Validate with serializer
            serializer = AutocompleteResponseSerializer(data=response_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error getting place suggestions for '{query}': {e}")
            return Response({
                'suggestions': [],
                'error': 'Failed to fetch suggestions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TripStatusAPIView(APIView):
    """
    API endpoint to check trip generation status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, trip_id):
        try:
            trip_request = get_object_or_404(TripPlanRequest, id=trip_id, user=request.user)
            
            # Check if the trip plan is already generated
            try:
                generated_plan = trip_request.generated_plan
                # Check if we have content (PDF is optional for display)
                if generated_plan.content and len(generated_plan.content.strip()) > 50:
                    response_data = {'status': 'completed'}
                else:
                    # Plan exists but incomplete - start regeneration
                    logger.info(f"Incomplete plan found for trip {trip_id}, starting regeneration")
                    from threading import Thread
                    from .views import generate_trip_plan_background
                    
                    thread = Thread(target=generate_trip_plan_background, 
                                  args=(trip_id, request.user.id))
                    thread.daemon = True
                    thread.start()
                    response_data = {'status': 'generating'}
                    
            except GeneratedPlan.DoesNotExist:
                # No plan exists - start background generation
                logger.info(f"No plan found for trip {trip_id}, starting generation")
                from threading import Thread
                from .views import generate_trip_plan_background
                
                thread = Thread(target=generate_trip_plan_background, 
                              args=(trip_id, request.user.id))
                thread.daemon = True
                thread.start()
                response_data = {'status': 'generating'}
            
            # Validate with serializer
            serializer = TripStatusSerializer(data=response_data)
            if serializer.is_valid():
                return Response(serializer.validated_data)
            else:
                return Response(response_data)
                
        except Exception as e:
            logger.error(f"Error checking trip status for {trip_id}: {e}")
            return Response({
                'status': 'error', 
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeneratePDFAPIView(APIView):
    """
    API endpoint for manually regenerating PDF files
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def post(self, request, trip_id):
        try:
            trip_request = get_object_or_404(TripPlanRequest, pk=trip_id, user=request.user)
            
            # Get the generated plan
            try:
                generated_plan = trip_request.generated_plan
                if not generated_plan.content:
                    return Response({
                        'success': False,
                        'error': 'No trip plan content found to generate PDF'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except GeneratedPlan.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'No trip plan found. Please generate a trip plan first.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            try:
                # Generate clean PDF using optimized service
                logger.info(f"Generating clean PDF for trip request {trip_id}")
                from .optimized_services import generate_clean_pdf
                import os
                
                pdf_content = generate_clean_pdf(generated_plan.content, trip_request.destination)
                
                # Save PDF file
                pdf_filename = f"trip_plan_{trip_request.id}.pdf"
                
                # Delete old PDF file if it exists
                if generated_plan.pdf_file:
                    try:
                        if os.path.exists(generated_plan.pdf_file.path):
                            os.remove(generated_plan.pdf_file.path)
                            logger.info(f"Deleted old PDF file for trip {trip_id}")
                    except Exception as cleanup_error:
                        logger.warning(f"Could not delete old PDF: {cleanup_error}")
                
                # Save new PDF file
                generated_plan.pdf_file.save(pdf_filename, pdf_content, save=True)
                
                logger.info(f"✅ PDF generated successfully for trip request {trip_id}")
                logger.info(f"PDF size: {generated_plan.pdf_file.size} bytes")
                
                response_data = {
                    'success': True,
                    'pdf_url': generated_plan.pdf_file.url,
                    'message': 'PDF generated successfully'
                }
                
                # Validate with serializer
                serializer = PDFGenerationSerializer(data=response_data)
                if serializer.is_valid():
                    return Response(serializer.validated_data)
                else:
                    return Response(response_data)
                
            except Exception as pdf_error:
                logger.error(f"Error generating PDF for trip {trip_id}: {pdf_error}")
                return Response({
                    'success': False,
                    'error': f'Error generating PDF: {str(pdf_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error in GeneratePDFAPIView for trip {trip_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CostDashboardAPIView(APIView):
    """
    API endpoint for cost monitoring data (admin only)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Only allow superusers to access cost data
        if not request.user.is_superuser:
            return Response({
                'error': 'Access denied. Admin privileges required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from .cost_monitor import cost_monitor
            
            # Get usage statistics
            usage = cost_monitor.get_daily_usage()
            recommendations = cost_monitor.get_cost_recommendation()
            
            response_data = {
                'usage': usage,
                'recommendations': recommendations
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error loading cost dashboard data: {e}")
            return Response({
                'error': 'Error loading cost dashboard data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
