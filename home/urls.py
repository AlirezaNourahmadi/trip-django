from django.urls import path, include
from . import views
from .views import (
    HomeView, TripRequestCreateView, TripRequestDetailView, TripRequestUpdateView,
    ChatbotView, ChatbotWithContextView, ProfileView, EditProfileView, RemoveProfilePictureView,
    CostDashboardView, TermsOfServiceView, PrivacyPolicyView
)
from .api_views import (
    TripStatusAPIView, PlacesAutocompleteAPIView, LocationPhotosAPIView, 
    GeneratePDFAPIView, CostDashboardAPIView
)

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("chatbot/", ChatbotView.as_view(), name="chatbot"),
    path("trip_request/", TripRequestCreateView.as_view(), name="trip_request_create"),
    path("trip_request/<int:pk>/", TripRequestDetailView.as_view(), name="trip_request_detail"),
    path("trip_request/<int:pk>/update/", TripRequestUpdateView.as_view(), name="trip_request_update"),
    path("chatbot/<int:trip_id>/", ChatbotWithContextView.as_view(), name="chatbot_with_context"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", EditProfileView.as_view(), name="edit_profile"),
    path("profile/picture/remove/", RemoveProfilePictureView.as_view(), name="remove_profile_picture"),
    path("cost-dashboard/", CostDashboardView.as_view(), name="cost_dashboard"),
    
    # API endpoints
    path("api/trip-status/<int:trip_id>/", TripStatusAPIView.as_view(), name="trip_status"),
    path("api/places-autocomplete/", PlacesAutocompleteAPIView.as_view(), name="places_autocomplete"),
    path("api/location-photos/", LocationPhotosAPIView.as_view(), name="location_photos"),
    path("api/generate-pdf/<int:trip_id>/", GeneratePDFAPIView.as_view(), name="generate_pdf"),
    
    # Legal pages
    path("terms-of-service/", TermsOfServiceView.as_view(), name="terms_of_service"),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy_policy"),
]
