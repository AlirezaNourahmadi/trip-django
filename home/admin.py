from django.contrib import admin
from .models import User, Destination, TripPlanRequest, GeneratedPlan
# Register your models here.
admin.site.register(User)
admin.site.register(Destination)
admin.site.register(TripPlanRequest)
admin.site.register(GeneratedPlan)