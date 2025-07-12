from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    pass

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
