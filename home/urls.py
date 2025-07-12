from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("chatbot/", ChatbotView.as_view(), name="chatbot"),
    path("trip_request/", TripRequestCreateView.as_view(), name="trip_request_create"),
    path("trip_request/<int:pk>/", TripRequestDetailView.as_view(), name="trip_request_detail"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
