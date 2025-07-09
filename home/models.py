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