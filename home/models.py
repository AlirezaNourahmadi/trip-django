from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    # Additional user preferences for personalized recommendations
    preferred_budget_range = models.CharField(max_length=50, blank=True, null=True)
    travel_style = models.CharField(max_length=100, blank=True, null=True)
    previous_destinations = models.TextField(blank=True, null=True)
    dietary_restrictions = models.CharField(max_length=200, blank=True, null=True)

class Destination(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="destination_images/")
    
    def __str__(self):
        return f"{self.name}, {self.country}"
    
class TripPlanRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE , related_name="trip_requests")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE , related_name="trip_requests")
    duration = models.IntegerField(help_text="Duration in days")
    budget = models.DecimalField(help_text="budget in chosen currency" , max_digits=10, decimal_places=2)
    number_of_travelers = models.IntegerField(default=1, help_text="Number of travelers")
    interests = models.TextField(blank=True, null=True, help_text="interests and activities")
    daily_budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Daily budget")
    transportation_preferences = models.CharField(max_length=255, blank=True, null=True, help_text="Transportation preferences")
    experience_style = models.CharField(max_length=255, blank=True, null=True, help_text="Experience style")
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_file = models.FileField(upload_to='trip_uploads/', blank=True, null=True)
    
    def __str__(self):
        return f"TripPlanRequest #{self.id} by {self.user}"
    
class GeneratedPlan(models.Model):
    trip_request = models.OneToOneField(TripPlanRequest, on_delete=models.CASCADE, related_name="generated_plan")
    content = models.TextField()
    pdf_file = models.FileField(upload_to='trip_pdfs/', blank=True, null=True)
    
    def __str__(self):
        return f"GeneratedPlan for request #{self.trip_request.id}"

class Location(models.Model):
    """Store location data with images and schedules"""
    name = models.CharField(max_length=255)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="locations")
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    image_file = models.ImageField(upload_to="location_images/", blank=True, null=True)
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    opening_hours = models.CharField(max_length=200, blank=True, null=True)
    best_time_to_visit = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)  # restaurant, attraction, hotel, etc.
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.destination.name}"

class UserTripHistory(models.Model):
    """Store user's trip history for personalized recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trip_history")
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    trip_date = models.DateField()
    satisfaction_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.destination.name} ({self.trip_date})"

class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('voice', 'Voice'),
    ]
    
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages', null=True, blank=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)  # For anonymous users
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True, null=True)
    file_attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    voice_attachment = models.FileField(upload_to='chat_voice/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..." if self.content else f"{self.sender}: {self.message_type} message"
