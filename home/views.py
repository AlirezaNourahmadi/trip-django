from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import TripPlanRequest, GeneratedPlan
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import TripPlanRequestForm
# Create your views here.

class HomeView(View):
    def get(self, request):
        return render(request, "home/index.html")


# TripRequestCreateView: for creating a trip plan request
class TripRequestCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = TripPlanRequestForm()
        return render(request, "home/trip_request_form.html", {"form": form})

    def post(self, request):
        form = TripPlanRequestForm(request.POST, request.FILES)
        if form.is_valid():
            trip_request = form.save(commit=False)
            trip_request.user = request.user
            trip_request.save()
            return HttpResponseRedirect(reverse("trip_request_detail", args=[trip_request.pk]))
        return render(request, "home/trip_request_form.html", {"form": form})


# TripRequestDetailView: for showing details of a trip plan request and its plan (if exists)
class TripRequestDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        trip_request = TripPlanRequest.objects.get(pk=pk)
        try:
            plan = trip_request.generated_plan
        except GeneratedPlan.DoesNotExist:
            plan = None
        return render(request, "home/trip_request_detail.html", {
            "trip_request": trip_request,
            "plan": plan
        })