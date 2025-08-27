from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image
import os
from django.conf import settings
from django.urls import reverse
# Create your models here.

def user_profile_picture_path(instance, filename):
    """Generate upload path for user profile pictures"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create filename as user_id.extension
    filename = f'profile_{instance.id}.{ext}'
    return os.path.join('profile_pictures', filename)

class User(AbstractUser):
    # Profile information
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="Tell us about yourself")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Profile picture
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path, 
        blank=True, 
        null=True,
        help_text="Upload your profile picture"
    )
    
    # Additional user preferences for personalized recommendations
    preferred_budget_range = models.CharField(max_length=50, blank=True, null=True)
    travel_style = models.CharField(max_length=100, blank=True, null=True)
    previous_destinations = models.TextField(blank=True, null=True)
    dietary_restrictions = models.CharField(max_length=200, blank=True, null=True)
    
    # Google OAuth fields
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    avatar_url = models.URLField(blank=True, null=True)
    is_google_user = models.BooleanField(default=False)
    google_profile_data = models.JSONField(default=dict, blank=True)
    
    # Profile completion tracking
    profile_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Override save to resize profile picture and update profile completion"""
        super().save(*args, **kwargs)
        
        # Resize profile picture if it exists
        if self.profile_picture:
            self.resize_profile_picture()
        
        # Update profile completion status
        self.update_profile_completion()
    
    def resize_profile_picture(self):
        """Resize profile picture to a standard size"""
        try:
            img_path = self.profile_picture.path
            img = Image.open(img_path)
            
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            
            # Resize image
            output_size = (300, 300)
            img.thumbnail(output_size, Image.Resampling.LANCZOS)
            
            # Save the resized image
            img.save(img_path, quality=95)
        except Exception as e:
            print(f"Error resizing profile picture for user {self.username}: {e}")
    
    def update_profile_completion(self):
        """Update profile completion status based on filled fields"""
        required_fields = [
            self.first_name,
            self.last_name,
            self.email,
        ]
        
        optional_fields = [
            self.bio,
            self.phone_number,
            self.location,
        ]
        
        # Check if all required fields are filled
        required_complete = all(field for field in required_fields)
        
        # Check if at least 2 optional fields are filled
        optional_complete = sum(1 for field in optional_fields if field) >= 2
        
        # Check if profile picture is set (either uploaded or from Google)
        has_picture = self.profile_picture or self.avatar_url
        
        # Profile is complete if all conditions are met
        new_completion_status = required_complete and optional_complete and has_picture
        
        if self.profile_completed != new_completion_status:
            self.profile_completed = new_completion_status
            # Save without calling the full save method to avoid recursion
            User.objects.filter(pk=self.pk).update(profile_completed=new_completion_status)
    
    def get_profile_picture_url(self):
        """Get profile picture URL, preferring uploaded picture over Google avatar"""
        if self.profile_picture:
            return self.profile_picture.url
        elif self.avatar_url:
            return self.avatar_url
        else:
            # Return default avatar
            return f"{settings.STATIC_URL}images/default_avatar.png"
    
    def get_display_name(self):
        """Get user's display name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    def get_profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        fields_to_check = [
            ('first_name', 1),
            ('last_name', 1),
            ('email', 1),
            ('bio', 1),
            ('phone_number', 1),
            ('date_of_birth', 1),
            ('location', 1),
            ('profile_picture', 1),
            ('avatar_url', 1),  # Alternative to profile_picture
        ]
        
        total_weight = 8  # Total possible points
        current_weight = 0
        
        for field_name, weight in fields_to_check:
            field_value = getattr(self, field_name)
            if field_value:
                current_weight += weight
                
                # Don't double count if both profile_picture and avatar_url exist
                if field_name == 'avatar_url' and self.profile_picture:
                    current_weight -= weight
        
        return min(100, int((current_weight / total_weight) * 100))
    
    def get_absolute_url(self):
        """Get URL for user profile"""
        return reverse('profile:view', kwargs={'username': self.username})
    
    def __str__(self):
        return self.get_display_name()

class Destination(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="destination_images/")
    
    def __str__(self):
        return f"{self.name}, {self.country}"
    
class TripPlanRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE , related_name="trip_requests")
    destination = models.CharField(max_length=255, help_text="Destination city or place")
    destination_country = models.CharField(max_length=255, blank=True, null=True, help_text="Destination country")
    destination_place_id = models.CharField(max_length=255, blank=True, null=True, help_text="Google Places ID")
    duration = models.IntegerField(help_text="Duration in days")
    budget = models.DecimalField(help_text="Budget (USD)" , max_digits=14, decimal_places=2)
    number_of_travelers = models.IntegerField(default=1, help_text="Number of travelers")
    interests = models.TextField(blank=True, null=True, help_text="interests and activities")
    daily_budget = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Daily budget (USD per person)")
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

class Ticket(models.Model):
    """Support ticket system for trip modifications and user assistance"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('trip_modification', 'Trip Modification'),
        ('destination_change', 'Destination Change'),
        ('budget_adjustment', 'Budget Adjustment'),
        ('itinerary_update', 'Itinerary Update'),
        ('general_support', 'General Support'),
        ('technical_issue', 'Technical Issue'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    trip_request = models.ForeignKey(TripPlanRequest, on_delete=models.CASCADE, related_name='tickets', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general_support')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data for context
    original_destination = models.CharField(max_length=255, blank=True, null=True)
    requested_changes = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket #{self.id}: {self.title} - {self.get_status_display()}"

class TicketMessage(models.Model):
    """Messages within a support ticket (chatbot conversation)"""
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('admin', 'Admin'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    message_type = models.CharField(max_length=10, default='text')
    file_attachment = models.FileField(upload_to='ticket_attachments/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # For bot responses - track what action was taken
    action_taken = models.CharField(max_length=50, blank=True, null=True)
    action_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message in Ticket #{self.ticket.id} by {self.sender}"

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





