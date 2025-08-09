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
from threading import Thread
from datetime import datetime

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
            
# Redirect to the loading page before generating the trip plan
            return render(request, "home/trip_loading.html", {
                "trip_request_id": trip_request.pk,
                "destination_name": trip_request.destination,
                "duration": trip_request.duration,
                "travelers": trip_request.number_of_travelers,
                "budget": trip_request.budget
            })
        return render(request, "home/trip_request_form.html", {"form": form})


# TripRequestDetailView: for showing details of a trip plan request and its plan (if exists)
class TripRequestDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        trip_request = TripPlanRequest.objects.get(pk=pk)
        try:
            plan = trip_request.generated_plan
        except GeneratedPlan.DoesNotExist:
            plan = None
        
        # Use enhanced template with photos if plan exists
        template_name = "home/trip_detail_enhanced.html" if plan else "home/trip_request_detail.html"
        
        return render(request, template_name, {
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

class TripRequestUpdateView(LoginRequiredMixin, View):
    """View for updating existing trip requests"""
    
    def get(self, request, pk):
        trip_request = get_object_or_404(TripPlanRequest, pk=pk, user=request.user)
        form = TripPlanRequestForm(instance=trip_request)
        return render(request, "home/trip_request_update.html", {
            "form": form,
            "trip_request": trip_request
        })
    
    def post(self, request, pk):
        trip_request = get_object_or_404(TripPlanRequest, pk=pk, user=request.user)
        form = TripPlanRequestForm(request.POST, request.FILES, instance=trip_request)
        
        if form.is_valid():
            updated_request = form.save()
            
            # Create a ticket for the update request
            from .models import Ticket
            ticket = Ticket.objects.create(
                user=request.user,
                trip_request=updated_request,
                title=f"Trip Update Request for {updated_request.destination}",
                description=f"User requested updates to their trip plan. Original request ID: {pk}",
                category='trip_modification',
                priority='medium'
            )
            
            messages.success(request, 'Your trip request has been updated successfully! A support ticket has been created.')
            return HttpResponseRedirect(reverse('trip_request_detail', args=[pk]))
        
        return render(request, "home/trip_request_update.html", {
            "form": form,
            "trip_request": trip_request
        })

class ChatbotWithContextView(LoginRequiredMixin, View):
    """Chatbot view with trip request context for personalized assistance"""
    
    def get(self, request, trip_id):
        trip_request = get_object_or_404(TripPlanRequest, pk=trip_id, user=request.user)
        
        # Get or create a ticket for this chat session
        from .models import Ticket, TicketMessage
        ticket, created = Ticket.objects.get_or_create(
            user=request.user,
            trip_request=trip_request,
            status__in=['open', 'in_progress'],
            defaults={
                'title': f'Chat Session for {trip_request.destination} Trip',
                'description': f'User initiated chat session for trip request #{trip_id}',
                'category': 'general_support',
                'priority': 'medium'
            }
        )
        
        # Get existing messages in this ticket
        messages = ticket.messages.all()
        
        return render(request, "home/chatbot_with_context.html", {
            "trip_request": trip_request,
            "ticket": ticket,
            "messages": messages
        })
    
    def post(self, request, trip_id):
        trip_request = get_object_or_404(TripPlanRequest, pk=trip_id, user=request.user)
        message = request.POST.get('message', '').strip()
        file_attachment = request.FILES.get('file_attachment')
        
        # Get or create ticket
        from .models import Ticket, TicketMessage
        ticket, created = Ticket.objects.get_or_create(
            user=request.user,
            trip_request=trip_request,
            status__in=['open', 'in_progress'],
            defaults={
                'title': f'Chat Session for {trip_request.destination} Trip',
                'description': f'User initiated chat session for trip request #{trip_id}',
                'category': 'general_support',
                'priority': 'medium'
            }
        )
        
        # Save user message
        user_message = TicketMessage.objects.create(
            ticket=ticket,
            sender='user',
            content=message,
            file_attachment=file_attachment,
            message_type='text' if message else 'file'
        )
        
        # Get trip context for AI
        trip_context = self.get_trip_context(trip_request)
        
        # Get chat history from this ticket
        chat_history = ticket.messages.all()
        
        # Generate AI response with trip context
        try:
            response_text = ai_service.generate_contextual_response(
                message=message,
                trip_context=trip_context,
                file_attachment=file_attachment,
                chat_history=chat_history,
                user=request.user
            )
        except Exception as e:
            logger.error(f"Error generating contextual AI response: {e}")
            response_text = "I'm having trouble connecting right now. Please try again in a moment!"
        
        # Save bot response
        TicketMessage.objects.create(
            ticket=ticket,
            sender='bot',
            content=response_text,
            message_type='text'
        )
        
        return JsonResponse({'response': response_text})
    
    def get_trip_context(self, trip_request):
        """Generate comprehensive trip context for AI"""
        context = {
            'trip_id': trip_request.id,
            'destination': trip_request.destination,
            'country': trip_request.destination_country,
            'duration': trip_request.duration,
            'budget': str(trip_request.budget),
            'number_of_travelers': trip_request.number_of_travelers,
            'interests': trip_request.interests,
            'daily_budget': str(trip_request.daily_budget) if trip_request.daily_budget else None,
            'transportation_preferences': trip_request.transportation_preferences,
            'experience_style': trip_request.experience_style,
            'created_at': trip_request.created_at.isoformat(),
        }
        
        # Add generated plan if exists
        try:
            plan = trip_request.generated_plan
            context['has_generated_plan'] = True
            context['generated_plan_content'] = plan.content[:1000]  # First 1000 chars
        except:
            context['has_generated_plan'] = False
        
        return context

def generate_trip_plan_background(trip_request_id, user_id):
    """Background function to generate trip plan"""
    try:
        trip_request = TripPlanRequest.objects.get(id=trip_request_id)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        try:
            # Generate initial trip plan
            initial_trip_plan = ai_service.generate_trip_plan(trip_request)
            
            # Enhance the trip plan with location images, schedules, and costs
            trip_plan_text = ai_service.generate_enhanced_response(
                initial_plan=initial_trip_plan,
                user=user,
                destination=trip_request.destination,
                number_of_travelers=trip_request.number_of_travelers
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating trip plan: {error_msg}")
            
            # Create a fallback trip plan
            trip_plan_text = f"""
🌟 Trip Plan for {trip_request.destination}

We encountered some technical difficulties generating your detailed itinerary, but here's a basic framework for your {trip_request.duration}-day trip:

📍 Destination: {trip_request.destination}
👥 Travelers: {trip_request.number_of_travelers}
💰 Budget: ${trip_request.budget}
⏱️ Duration: {trip_request.duration} days

🎯 Your Interests: {trip_request.interests or 'Explore and discover'}

Day 1: Arrival and Initial Exploration
• Arrive at your destination
• Check into accommodation
• Explore the local area
• Try local cuisine for dinner

Day 2-{max(2, trip_request.duration-1)}: Main Activities
• Visit top attractions based on your interests
• Experience local culture and traditions
• Try recommended restaurants
• Take photos and create memories

Day {trip_request.duration}: Departure
• Final activities or shopping
• Prepare for departure
• Safe travels home!

💡 Note: This is a basic itinerary due to temporary technical issues. For a detailed, personalized plan, please try generating your trip plan again later or contact our support team.

🗺️ We recommend researching specific attractions, restaurants, and activities in {trip_request.destination} that match your interests: {trip_request.interests or 'general tourism'}
            """
        
        try:
            # Generate PDF file from trip plan text with Google Maps links
            pdf_content = generate_trip_plan_pdf(trip_plan_text, trip_request.destination)
            
            # Save GeneratedPlan instance
            generated_plan, created = GeneratedPlan.objects.get_or_create(trip_request=trip_request)
            generated_plan.content = trip_plan_text
            generated_plan.pdf_file.save(f"trip_plan_{trip_request.id}.pdf", pdf_content)
            generated_plan.save()
            
            logger.info(f"Trip plan generated successfully for request {trip_request_id}")
            
        except Exception as pdf_error:
            logger.error(f"Error generating PDF for request {trip_request_id}: {pdf_error}")
            # Save just the text content without PDF
            generated_plan, created = GeneratedPlan.objects.get_or_create(trip_request=trip_request)
            generated_plan.content = trip_plan_text
            generated_plan.save()
        
    except TripPlanRequest.DoesNotExist:
        logger.error(f"Trip request {trip_request_id} not found")
    except Exception as e:
        logger.error(f"Unexpected error in generate_trip_plan_background for request {trip_request_id}: {e}")

class TripStatusAPIView(View):
    """API endpoint to check trip generation status"""
    
    def get(self, request, trip_id):
        try:
            trip_request = TripPlanRequest.objects.get(id=trip_id)
            
            # Check if the trip plan is already generated
            try:
                generated_plan = trip_request.generated_plan
                if generated_plan.content and generated_plan.pdf_file:
                    return JsonResponse({'status': 'completed'})
                else:
                    return JsonResponse({'status': 'processing'})
            except GeneratedPlan.DoesNotExist:
                # Start background generation if not already started
                thread = Thread(target=generate_trip_plan_background, 
                              args=(trip_id, request.user.id))
                thread.daemon = True
                thread.start()
                return JsonResponse({'status': 'processing'})
                
        except TripPlanRequest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Trip request not found'})
        except Exception as e:
            logger.error(f"Error checking trip status: {e}")
            return JsonResponse({'status': 'error', 'message': 'Internal server error'})

class PlacesAutocompleteAPIView(View):
    """API endpoint for Google Places autocomplete"""
    
    def get(self, request):
        query = request.GET.get('query', '').strip()
        if not query or len(query) < 2:
            return JsonResponse({'suggestions': []})
        
        try:
            from .services import gmaps_service
            
            # Use Google Places API for autocomplete
            suggestions = gmaps_service.get_place_suggestions(query)
            
            return JsonResponse({
                'suggestions': suggestions
            })
            
        except Exception as e:
            logger.error(f"Error getting place suggestions: {e}")
            return JsonResponse({
                'suggestions': [],
                'error': 'Failed to fetch suggestions'
            })

class LocationPhotosAPIView(View):
    """API endpoint for fetching location photos from Google Places"""
    
    def get(self, request):
        location_name = request.GET.get('location', '').strip()
        destination_city = request.GET.get('destination', '').strip()
        
        if not location_name:
            return JsonResponse({'error': 'Location name is required'}, status=400)
        
        try:
            from .services import gmaps_service
            
            # Get place details including photos
            place_details = gmaps_service.get_place_details(location_name, destination_city)
            
            if not place_details:
                return JsonResponse({
                    'location': location_name,
                    'photos': [],
                    'rating': None,
                    'formatted_address': None,
                    'message': 'Location not found'
                })
            
            return JsonResponse({
                'location': location_name,
                'place_id': place_details.get('place_id'),
                'name': place_details.get('name'),
                'photos': place_details.get('photos', []),
                'rating': place_details.get('rating'),
                'formatted_address': place_details.get('formatted_address'),
                'types': place_details.get('types', []),
                'maps_link': f"https://maps.google.com/?q=place_id:{place_details.get('place_id')}" if place_details.get('place_id') else None
            })
            
        except Exception as e:
            logger.error(f"Error getting location photos for {location_name}: {e}")
            return JsonResponse({
                'error': 'Failed to fetch location photos',
                'location': location_name,
                'photos': []
            }, status=500)
