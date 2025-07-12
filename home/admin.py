from django.contrib import admin
from .models import User, Destination, TripPlanRequest, GeneratedPlan, ChatMessage

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['name', 'country']
    search_fields = ['name', 'country']
    list_filter = ['country']

@admin.register(TripPlanRequest)
class TripPlanRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'destination', 'duration', 'budget', 'created_at']
    search_fields = ['user__username', 'destination__name']
    list_filter = ['destination', 'created_at']
    readonly_fields = ['created_at']

@admin.register(GeneratedPlan)
class GeneratedPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip_request', 'get_user', 'get_destination']
    search_fields = ['trip_request__user__username', 'trip_request__destination__name']
    
    def get_user(self, obj):
        return obj.trip_request.user.username
    get_user.short_description = 'User'
    
    def get_destination(self, obj):
        return obj.trip_request.destination.name
    get_destination.short_description = 'Destination'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'message_type', 'content_preview', 'user', 'timestamp']
    search_fields = ['content', 'user__username']
    list_filter = ['sender', 'message_type', 'timestamp']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        if obj.content:
            return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return f'{obj.message_type} message'
    content_preview.short_description = 'Content Preview'
