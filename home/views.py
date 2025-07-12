from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from .models import TripPlanRequest, GeneratedPlan, ChatMessage
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from .forms import TripPlanRequestForm, CustomUserCreationForm, ChatMessageForm
import json
import uuid
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

class ChatbotView(View):
    def get(self, request):
        return render(request, "home/chatbot.html")
    
    def post(self, request):
        message = request.POST.get('message', '').strip()
        file_attachment = request.FILES.get('file_attachment')
        voice_attachment = request.FILES.get('voice_attachment')
        
        # Get or create session ID for anonymous users
        session_id = request.session.get('chat_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['chat_session_id'] = session_id
        
        # Save user message
        user_message = ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id if not request.user.is_authenticated else None,
            sender='user',
            content=message,
            file_attachment=file_attachment,
            voice_attachment=voice_attachment,
            message_type='text' if message else ('voice' if voice_attachment else 'file')
        )
        
        # Generate AI response (placeholder - you can integrate with your LLM here)
        response_text = self.generate_ai_response(message, file_attachment, voice_attachment)
        
        # Save bot response
        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id if not request.user.is_authenticated else None,
            sender='bot',
            content=response_text,
            message_type='text'
        )
        
        return JsonResponse({'response': response_text})
    
    def generate_ai_response(self, message, file_attachment, voice_attachment):
        """Generate AI response based on message and attachments"""
        # This is a placeholder function. You should integrate with your LLM API here
        responses = {
            'file': "I can see you've attached a file. I can help you analyze travel documents, itineraries, or any other travel-related files. What would you like me to help you with?",
            'voice': "I received your voice message. I can help you with travel planning, destination recommendations, budget planning, and more. What specific aspect of your trip would you like assistance with?",
            'general': [
                "I'm here to help you plan your perfect trip! I can assist with destination recommendations, budget planning, itinerary creation, and travel tips. What would you like to know?",
                "Great question! As your travel assistant, I can help you with booking strategies, local customs, weather information, and much more. How can I make your travel experience better?",
                "I'd be happy to help you with your travel plans! Whether you need advice on accommodations, transportation, activities, or cultural insights, I'm here for you.",
            ]
        }
        
        if file_attachment:
            return responses['file']
        elif voice_attachment:
            return responses['voice']
        elif message:
            # Simple keyword-based responses (you should replace this with actual LLM integration)
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['budget', 'money', 'cost', 'price', 'expensive']):
                return "For budget planning, I recommend setting aside 20% extra for unexpected expenses. I can help you create a detailed budget breakdown based on your destination, duration, and travel style. What's your target budget range?"
            
            elif any(word in message_lower for word in ['destination', 'where', 'place', 'country', 'city']):
                return "Choosing the right destination depends on your interests, budget, and travel dates. Are you looking for adventure, relaxation, culture, or maybe a mix? Also, what time of year are you planning to travel?"
            
            elif any(word in message_lower for word in ['hotel', 'accommodation', 'stay', 'booking']):
                return "For accommodations, I recommend booking at least 2-3 months in advance for better rates. Consider factors like location, amenities, and cancellation policies. What type of accommodation are you considering?"
            
            elif any(word in message_lower for word in ['flight', 'airline', 'plane', 'airport']):
                return "For flights, Tuesday and Wednesday are often the cheapest days to fly. Book domestic flights 1-3 months ahead and international flights 2-8 months ahead. Would you like tips for finding the best flight deals?"
            
            else:
                import random
                return random.choice(responses['general'])
        
        return "I'm here to help with your travel planning! Feel free to ask me anything about destinations, budgets, accommodations, or travel tips."

class CustomLoginView(LoginView):
    template_name = 'home/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('home'))
        form = CustomUserCreationForm()
        return render(request, 'home/register.html', {'form': form})
    
    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return HttpResponseRedirect(reverse('home'))
        return render(request, 'home/register.html', {'form': form})

class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'home/profile.html')
