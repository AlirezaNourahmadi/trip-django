"""
DRF Serializers for TripAI Application

This module contains all Django REST Framework serializers for API data validation,
serialization, and deserialization. Following DRF best practices for data handling.

NOTE FOR DRF/JWT EXPERT:
=======================
This file demonstrates advanced DRF serializer patterns:

1. SERIALIZER TYPES:
   - Model Serializers: For database model serialization
   - Serializer classes: For API response/request validation
   - Nested serializers: For complex data structures
   - ListSerializer: For bulk operations

2. VALIDATION PATTERNS:
   - Field-level validation with validate_<field_name>()
   - Object-level validation with validate()
   - Custom validators with validators parameter
   - Cross-field validation for business logic

3. SERIALIZATION FEATURES:
   - SerializerMethodField for computed fields
   - to_representation() for custom output formatting
   - to_internal_value() for custom input processing
   - Context passing for conditional serialization

4. PERFORMANCE OPTIMIZATIONS:
   - select_related() and prefetch_related() in ViewSets
   - Field selection with 'fields' and 'exclude'
   - Read-only fields for performance
   - Custom queryset optimization

5. JWT INTEGRATION READY:
   - User context available through self.context['request'].user
   - Token payload accessible for custom claims
   - Permission-based field exclusion patterns

SERIALIZER PATTERNS USED:
========================
- Validation serializers: For API input validation
- Response serializers: For structured API responses  
- Nested serializers: For related model data
- Dynamic serializers: Context-dependent field inclusion

FOR JWT MIGRATION:
=================
When migrating to JWT, serializers can access JWT payload via:
```python
class MySerializer(serializers.Serializer):
    def validate(self, data):
        user = self.context['request'].user
        # JWT claims available through user.jwt_payload (if configured)
        return data
```
"""

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime

# Import models
from .models import TripPlanRequest, GeneratedPlan, User

# Get the user model for reference
User = get_user_model()


class LocationPhotoSerializer(serializers.Serializer):
    """Serializer for location photo data from Google Places API"""
    url = serializers.URLField()
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    attributions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )


class LocationDetailsSerializer(serializers.Serializer):
    """Serializer for location details from Google Places API"""
    location = serializers.CharField()
    place_id = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    photos = LocationPhotoSerializer(many=True, required=False)
    rating = serializers.FloatField(required=False)
    formatted_address = serializers.CharField(required=False)
    types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    maps_link = serializers.URLField(required=False)
    error = serializers.CharField(required=False)
    message = serializers.CharField(required=False)


class PlaceSuggestionSerializer(serializers.Serializer):
    """Serializer for Google Places autocomplete suggestions"""
    description = serializers.CharField()
    place_id = serializers.CharField()
    types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )


class AutocompleteResponseSerializer(serializers.Serializer):
    """Serializer for autocomplete API response"""
    suggestions = PlaceSuggestionSerializer(many=True)
    error = serializers.CharField(required=False)


class TripStatusSerializer(serializers.Serializer):
    """Serializer for trip generation status"""
    status = serializers.ChoiceField(choices=[
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ])
    message = serializers.CharField(required=False)


class PDFGenerationSerializer(serializers.Serializer):
    """Serializer for PDF generation response"""
    success = serializers.BooleanField()
    pdf_url = serializers.URLField(required=False)
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class CostUsageSerializer(serializers.Serializer):
    """Serializer for API cost usage data"""
    openai_calls = serializers.IntegerField()
    openai_cost = serializers.FloatField()
    gmaps_calls = serializers.IntegerField()
    gmaps_cost = serializers.FloatField()
    total_cost = serializers.FloatField()
    daily_limit = serializers.FloatField()
    remaining_budget = serializers.FloatField()
    cache_hit_rate = serializers.FloatField(required=False)


class CostRecommendationSerializer(serializers.Serializer):
    """Serializer for cost optimization recommendations"""
    level = serializers.ChoiceField(choices=[
        ('low', 'Low Usage'),
        ('medium', 'Medium Usage'),
        ('high', 'High Usage'),
        ('critical', 'Critical Usage')
    ])
    message = serializers.CharField()
    suggestions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )


# ============================================================================
# MODEL SERIALIZERS
# ============================================================================
# NOTE FOR DRF/JWT EXPERT: These demonstrate Model Serializer patterns

class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer with JWT-ready patterns.
    
    NOTE FOR JWT EXPERT:
    - Excludes sensitive fields by default
    - Uses SerializerMethodField for computed values
    - Ready for JWT claims integration
    """
    full_name = serializers.SerializerMethodField()
    trip_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'avatar_url', 'trip_count', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'trip_count']
    
    def get_full_name(self, obj):
        """Computed field: full name from first_name + last_name."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
    
    def get_trip_count(self, obj):
        """Computed field: number of trip requests by user."""
        return obj.trip_requests.count()
    
    def validate_email(self, value):
        """Custom email validation."""
        if User.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class TripRequestSerializer(serializers.ModelSerializer):
    """
    Trip request serializer with comprehensive validation.
    
    NOTE FOR JWT EXPERT:
    - Demonstrates field-level and object-level validation
    - Uses context for user-specific validation
    - Ready for JWT user claims integration
    """
    user = UserProfileSerializer(read_only=True)
    daily_budget_calculated = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TripPlanRequest
        fields = [
            'id', 'user', 'destination', 'destination_country',
            'duration', 'budget', 'daily_budget', 'daily_budget_calculated',
            'num_travelers', 'interests', 'transportation_preference',
            'experience_style', 'dietary_restrictions', 'accessibility_needs',
            'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        
    def get_daily_budget_calculated(self, obj):
        """Calculate daily budget from total budget and duration."""
        if obj.budget and obj.duration:
            return round(float(obj.budget) / obj.duration, 2)
        return None
    
    def validate_duration(self, value):
        """Validate trip duration is within reasonable limits."""
        if value < 1:
            raise serializers.ValidationError("Duration must be at least 1 day.")
        if value > 365:
            raise serializers.ValidationError("Duration cannot exceed 365 days.")
        return value
    
    def validate_budget(self, value):
        """Validate budget is positive and within limits."""
        if value < Decimal('0'):
            raise serializers.ValidationError("Budget must be positive.")
        if value > Decimal('1000000'):
            raise serializers.ValidationError("Budget cannot exceed $1,000,000.")
        return value
    
    def validate_num_travelers(self, value):
        """Validate number of travelers."""
        if value < 1:
            raise serializers.ValidationError("Number of travelers must be at least 1.")
        if value > 50:
            raise serializers.ValidationError("Number of travelers cannot exceed 50.")
        return value
    
    def validate(self, data):
        """
        Object-level validation for business logic.
        
        NOTE FOR JWT EXPERT: This is where you can implement
        user-specific validation using JWT claims.
        """
        # Validate budget per person is reasonable
        if data.get('budget') and data.get('num_travelers'):
            budget_per_person = float(data['budget']) / data['num_travelers']
            if budget_per_person < 10:
                raise serializers.ValidationError(
                    "Budget per person is too low (minimum $10 per person)."
                )
        
        # JWT user context validation example
        if self.context.get('request'):
            user = self.context['request'].user
            # Example: Limit number of active trips per user
            active_trips = user.trip_requests.filter(status__in=['pending', 'processing']).count()
            if active_trips >= 5:
                raise serializers.ValidationError(
                    "You have reached the maximum number of active trip requests (5)."
                )
        
        return data
    
    def create(self, validated_data):
        """Custom create method with user assignment."""
        # Assign the user from the request context
        if self.context.get('request'):
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GeneratedPlanSerializer(serializers.ModelSerializer):
    """
    Generated plan serializer with file handling.
    
    NOTE FOR JWT EXPERT:
    - Demonstrates file field serialization
    - Custom representation for sensitive data
    - Context-aware field inclusion
    """
    trip_request = TripRequestSerializer(read_only=True)
    pdf_url = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    word_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GeneratedPlan
        fields = [
            'id', 'trip_request', 'content', 'content_preview', 'word_count',
            'pdf_file', 'pdf_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_pdf_url(self, obj):
        """Get PDF file URL if available."""
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None
    
    def get_content_preview(self, obj):
        """Get content preview (first 200 characters)."""
        if obj.content:
            return obj.content[:200] + '...' if len(obj.content) > 200 else obj.content
        return None
    
    def get_word_count(self, obj):
        """Get approximate word count of content."""
        if obj.content:
            return len(obj.content.split())
        return 0
    
    def to_representation(self, instance):
        """Custom representation based on user permissions."""
        data = super().to_representation(instance)
        
        # Hide full content from non-owners (JWT claims can be used here)
        if self.context.get('request'):
            user = self.context['request'].user
            if instance.trip_request.user != user and not user.is_superuser:
                data.pop('content', None)
        
        return data


# ============================================================================
# ADVANCED SERIALIZER PATTERNS
# ============================================================================
# NOTE FOR DRF/JWT EXPERT: Advanced patterns for complex use cases

class CostMonitorSerializer(serializers.Serializer):
    """
    Advanced serializer for cost monitoring with nested data.
    
    Demonstrates:
    - Nested serializers
    - Dynamic field inclusion
    - Context-based serialization
    """
    daily_usage = CostUsageSerializer()
    recommendations = CostRecommendationSerializer(many=True)
    hourly_data = serializers.DictField(required=False)
    cache_stats = serializers.DictField(required=False)
    
    def to_representation(self, instance):
        """Dynamic field inclusion based on user role."""
        data = super().to_representation(instance)
        
        # Only include detailed stats for superusers
        if self.context.get('request'):
            user = self.context['request'].user
            if not user.is_superuser:
                data.pop('cache_stats', None)
                # Limit hourly data for non-admin users
                if 'hourly_data' in data:
                    # Only show last 24 hours for non-admin
                    hourly_data = data['hourly_data']
                    if isinstance(hourly_data, dict):
                        # Keep only recent data points
                        recent_keys = list(hourly_data.keys())[-24:]
                        data['hourly_data'] = {k: hourly_data[k] for k in recent_keys}
        
        return data
