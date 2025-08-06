from django.urls import path
from . import views
from .views import (
    HomeView, TripRequestCreateView, TripRequestDetailView, TripRequestUpdateView,
    ChatbotView, ChatbotWithContextView, CustomLoginView, CustomLogoutView, RegisterView, ProfileView,
    TripStatusAPIView, PlacesAutocompleteAPIView
)

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("chatbot/", ChatbotView.as_view(), name="chatbot"),
    path("trip_request/", TripRequestCreateView.as_view(), name="trip_request_create"),
    path("trip_request/<int:pk>/", TripRequestDetailView.as_view(), name="trip_request_detail"),
    path("trip_request/<int:pk>/update/", TripRequestUpdateView.as_view(), name="trip_request_update"),
    path("chatbot/<int:trip_id>/", ChatbotWithContextView.as_view(), name="chatbot_with_context"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("api/trip-status/<int:trip_id>/", TripStatusAPIView.as_view(), name="trip_status"),
    path("api/places-autocomplete/", PlacesAutocompleteAPIView.as_view(), name="places_autocomplete"),
]
