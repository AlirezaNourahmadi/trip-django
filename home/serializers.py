from rest_framework import serializers
from .models import TripPlanRequest, GeneratedPlan


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
