from django.shortcuts import render, get_object_or_404
from django.views import View
from .services import generate_trip_plan_pdf
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from .models import TripPlanRequest, GeneratedPlan, ChatMessage
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from .forms import TripPlanRequestForm, CustomUserCreationForm, ChatMessageForm
from .services import ai_service
import json
import uuid
import logging

logger = logging.getLogger(__name__)
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

            # Generate trip plan text using AIService
            
            initial_trip_plan = ai_service.generate_trip_plan(trip_request)
            
            # Enhance the trip plan with location images, schedules, and costs
            trip_plan_text = ai_service.generate_enhanced_response(
                initial_plan=initial_trip_plan,
                user=request.user if request.user.is_authenticated else None,
                destination=trip_request.destination.name,
                number_of_travelers=trip_request.number_of_travelers
            )

            # Generate PDF file from trip plan text
            pdf_content = generate_trip_plan_pdf(trip_plan_text)

            # Save GeneratedPlan instance
            from .models import GeneratedPlan
            generated_plan, created = GeneratedPlan.objects.get_or_create(trip_request=trip_request)
            generated_plan.content = trip_plan_text
            generated_plan.pdf_file.save(f"trip_plan_{trip_request.id}.pdf", pdf_content)
            generated_plan.save()

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
        
        # Get chat history for context
        chat_history = self.get_chat_history(request, session_id)
        
        # Generate AI response using OpenAI GPT-4
        try:
            response_text = ai_service.generate_response(
                message=message,
                file_attachment=file_attachment,
                voice_attachment=voice_attachment,
                chat_history=chat_history
            )
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            response_text = "I'm having trouble connecting to my AI brain right now. Please try again in a moment!"
        
        # Save bot response
        ChatMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id if not request.user.is_authenticated else None,
            sender='bot',
            content=response_text,
            message_type='text'
        )
        
        return JsonResponse({'response': response_text})
    
    def get_chat_history(self, request, session_id):
        """Get recent chat history for context"""
        if request.user.is_authenticated:
            return ChatMessage.objects.filter(user=request.user).order_by('timestamp')
        else:
            return ChatMessage.objects.filter(session_id=session_id).order_by('timestamp')

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
