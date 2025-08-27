from django.shortcuts import render, get_object_or_404
from django.views import View
from .services import generate_trip_plan_pdf
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from .models import TripPlanRequest, GeneratedPlan, ChatMessage, User
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from .forms import (
    TripPlanRequestForm, CustomUserCreationForm, ChatMessageForm,
    ProfilePictureForm, PersonalInfoForm, TravelPreferencesForm, CustomPasswordChangeForm
)
from .services import ai_service
import json
import uuid
import logging
import os
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

            # Redirect directly to loading page - trip generation happens in background
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


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        # Get user's trip requests with generated plans and tickets
        trip_requests = request.user.trip_requests.all().order_by('-created_at')
        
        # Get user's tickets
        tickets = request.user.tickets.all().order_by('-created_at')
        
        # Prepare trip data with PDF info
        trip_data = []
        for trip in trip_requests:
            trip_info = {
                'trip': trip,
                'has_plan': False,
                'has_pdf': False,
                'pdf_url': None,
                'ticket_count': trip.tickets.count()
            }
            
            try:
                plan = trip.generated_plan
                trip_info['has_plan'] = bool(plan.content)
                if plan.pdf_file:
                    trip_info['has_pdf'] = True
                    trip_info['pdf_url'] = plan.pdf_file.url
            except:
                pass
            
            trip_data.append(trip_info)
        
        # Enhanced profile data
        user = request.user
        profile_completion = user.get_profile_completion_percentage()
        profile_picture_url = user.get_profile_picture_url()
        display_name = user.get_display_name()
        
        context = {
            'trip_data': trip_data,
            'tickets': tickets,
            'profile_user': user,
            'is_own_profile': True,
            'profile_completion': profile_completion,
            'profile_picture_url': profile_picture_url,
            'display_name': display_name,
            'user': user,  # Keep for compatibility
        }
        
        return render(request, 'home/profile.html', context)

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
    """Cost-optimized background function using new optimized services"""
    try:
        # Import cost-optimized function
        from .optimized_services import cost_optimized_trip_generation
        cost_optimized_trip_generation(trip_request_id, user_id)
        
    except Exception as e:
        logger.error(f"Error in optimized trip generation: {e}")
        # Fallback to template-based generation
        try:
            from .models import TripPlanRequest, GeneratedPlan
            from .optimized_services import generate_template_fallback, generate_clean_pdf
            
            trip_request = TripPlanRequest.objects.get(id=trip_request_id)
            fallback_content = generate_template_fallback(trip_request)
            
            plan, created = GeneratedPlan.objects.get_or_create(
                trip_request=trip_request,
                defaults={'content': fallback_content}
            )
            
            plan.content = fallback_content
            pdf_content = generate_clean_pdf(fallback_content, trip_request.destination)
            plan.pdf_file.save(f"trip_plan_{trip_request_id}.pdf", pdf_content)
            plan.save()
            
            logger.info(f"✅ Fallback plan generated for {trip_request_id}")
            
        except Exception as fallback_error:
            logger.error(f"Even fallback generation failed: {fallback_error}")


class CostDashboardView(LoginRequiredMixin, View):
    """Dashboard for monitoring API costs (admin users only)"""
    
    def get(self, request):
        # Only allow superusers to view cost dashboard
        if not request.user.is_superuser:
            messages.error(request, "Access denied. Admin privileges required.")
            return HttpResponseRedirect(reverse('home'))
        
        try:
            from .cost_monitor import cost_monitor
            
            # Get usage statistics
            raw_usage = cost_monitor.get_daily_usage()
            raw_recommendations = cost_monitor.get_cost_recommendation()
            hourly_usage = cost_monitor.get_hourly_usage()
            
            # Format usage data for template
            usage = {
                'openai': raw_usage.get('openai', {'calls': 0, 'cost': 0.0, 'limit': 100}),
                'google_maps': raw_usage.get('google_maps', {'calls': 0, 'cost': 0.0, 'limit': 100}),
                'google_places': raw_usage.get('google_places', {'calls': 0, 'cost': 0.0, 'limit': 100}),
                'total_cost': raw_usage.get('total_cost', 0.0),
                'daily_limit': 5.00,  # $5 daily budget
                'cache_hit_rate': raw_usage.get('cache_stats', {}).get('hit_rate', 0.0),
                'hourly_data': hourly_usage
            }
            
            # Format recommendations for template
            total_cost = usage['total_cost']
            if total_cost > 3.0:
                level = 'critical'
                message = 'Critical: Daily budget almost exceeded!'
            elif total_cost > 2.0:
                level = 'high' 
                message = 'High usage detected - consider optimization'
            elif total_cost > 1.0:
                level = 'medium'
                message = 'Moderate usage - monitoring recommended'
            else:
                level = 'low'
                message = 'Usage is within optimal range'
            
            recommendations = {
                'level': level,
                'message': message,
                'suggestions': raw_recommendations
            }
            
            return render(request, 'home/cost_dashboard.html', {
                'usage': usage,
                'recommendations': recommendations,
                'hourly_data_json': json.dumps(hourly_usage)  # Serialize for JavaScript
            })
            
        except Exception as e:
            logger.error(f"Error loading cost dashboard: {e}")
            messages.error(request, f"Error loading cost dashboard: {str(e)}")
            return HttpResponseRedirect(reverse('home'))


class TermsOfServiceView(View):
    """Terms of Service page"""
    
    def get(self, request):
        return render(request, 'legal/terms_of_service.html')


class PrivacyPolicyView(View):
    """Privacy Policy page"""
    
    def get(self, request):
        return render(request, 'legal/privacy_policy.html')


# Profile Editing Views
class EditProfileView(LoginRequiredMixin, View):
    """Edit user profile - main page with tabs"""
    
    def get(self, request):
        context = {
            'personal_form': PersonalInfoForm(instance=request.user),
            'picture_form': ProfilePictureForm(instance=request.user),
            'travel_form': TravelPreferencesForm(instance=request.user),
            'password_form': CustomPasswordChangeForm(user=request.user),
            'profile_completion': request.user.get_profile_completion_percentage(),
            'user': request.user,
        }
        
        return render(request, 'home/edit_profile.html', context)
    
    def post(self, request):
        # Handle form submissions based on which form was submitted
        form_type = request.POST.get('form_type')
        
        if form_type == 'personal_info':
            form = PersonalInfoForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Personal information updated successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif form_type == 'profile_picture':
            form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                user = form.save()
                messages.success(request, 'Profile picture updated successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif form_type == 'travel_preferences':
            form = TravelPreferencesForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Travel preferences updated successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        elif form_type == 'change_password':
            from django.contrib.auth import update_session_auth_hash
            form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password changed successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        return HttpResponseRedirect(reverse('edit_profile'))


class RemoveProfilePictureView(LoginRequiredMixin, View):
    """Remove user's profile picture"""
    
    def post(self, request):
        if request.user.profile_picture:
            # Delete the file
            request.user.profile_picture.delete()
            request.user.save()
            messages.success(request, 'Profile picture removed successfully!')
        else:
            messages.info(request, 'No profile picture to remove.')
        
        return HttpResponseRedirect(reverse('edit_profile'))

