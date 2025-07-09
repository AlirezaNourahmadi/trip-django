from django.urls import path
from . import views
from .views import *
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("trip_request/", TripRequestCreateView.as_view(), name="trip_request_create"),
    path("trip_request/<int:pk>/", TripRequestDetailView.as_view(), name="trip_request_detail"),
    
]
