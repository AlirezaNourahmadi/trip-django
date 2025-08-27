import os
import base64
from django.conf import settings
from openai import OpenAI
import logging
import io
import re
import urllib.parse
import urllib.request
import googlemaps
from django.core.files.base import ContentFile
from concurrent.futures import ThreadPoolExecutor
import asyncio
from .models import UserTripHistory
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, blue
from reportlab.lib.units import inch
from datetime import datetime
import html



logger = logging.getLogger(__name__)

class GoogleMapsService:
    """Service for Google Maps API integration"""
    
    def __init__(self):
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    
    def get_place_details(self, location_name, destination_city=None):
        """Get place details including coordinates and place_id"""
        try:
            # Search for the place
            query = f"{location_name}"
            if destination_city:
                query += f", {destination_city}"
            
            places_result = self.gmaps.places(query=query)
            
            if places_result['results']:
                place = places_result['results'][0]
                place_details = {
                    'place_id': place.get('place_id'),
                    'name': place.get('name'),
                    'formatted_address': place.get('formatted_address'),
                    'location': place.get('geometry', {}).get('location', {}),
                    'rating': place.get('rating'),
                    'types': place.get('types', []),
                    'photos': []
                }
                
                # Get detailed information including photos
                if place.get('place_id'):
                    try:
                        # Get photos using the correct field name
                        detailed_place = self.gmaps.place(
                            place_id=place['place_id'],
                            fields=['name', 'photo', 'rating', 'formatted_address', 'geometry', 'type']
                        )
                        
                        logger.info(f"Place details for {location_name}: {list(detailed_place['result'].keys())}")
                        
                        # Check for photos field - API returns 'photos' in result, not 'photo'
                        photos_data = None
                        if 'photos' in detailed_place['result']:
                            photos_data = detailed_place['result']['photos']
                            logger.info(f"Found 'photos' field with {len(photos_data)} photos")
                        elif 'photo' in detailed_place['result']:
                            photos_data = detailed_place['result']['photo']
                            logger.info(f"Found 'photo' field with {len(photos_data)} photos")
                        else:
                            logger.warning(f"No photo field found for {location_name}")
                        
                        if photos_data:
                            # Get up to 3 photos for each location
                            photos = photos_data[:3]
                            for photo in photos:
                                photo_reference = photo.get('photo_reference')
                                if photo_reference:
                                    # Create photo URL
                                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={settings.GOOGLE_MAPS_API_KEY}"
                                    place_details['photos'].append({
                                        'url': photo_url,
                                        'width': photo.get('width', 400),
                                        'height': photo.get('height', 300),
                                        'attributions': photo.get('html_attributions', [])
                                    })
                                    logger.info(f"Added photo URL for {location_name}: {photo_url}")
                                else:
                                    logger.warning(f"No photo_reference found in photo data: {photo}")
                        
                    except Exception as photo_error:
                        logger.warning(f"Error fetching photos for {location_name}: {photo_error}")
                
                return place_details
        except Exception as e:
            logger.error(f"Error getting place details for {location_name}: {e}")
        return None
    
    def generate_google_maps_link(self, location_name, destination_city=None):
        """Generate Google Maps link for a location"""
        try:
            place_details = self.get_place_details(location_name, destination_city)
            if place_details and place_details.get('place_id'):
                # Create a Google Maps link using place_id
                return f"https://maps.google.com/?q=place_id:{place_details['place_id']}"
            else:
                # Fallback to search-based link
                query = urllib.parse.quote(f"{location_name} {destination_city or ''}")
                return f"https://maps.google.com/?q={query}"
        except Exception as e:
            logger.error(f"Error generating Google Maps link for {location_name}: {e}")
            # Fallback to simple search link
            query = urllib.parse.quote(f"{location_name} {destination_city or ''}")
            return f"https://maps.google.com/?q={query}"
    
    def extract_locations_from_text(self, text):
        """Extract potential location names from text using regex patterns"""
        # Process text line by line to avoid multiline capture issues
        lines = text.split('\n')
        locations = set()
        
        # Common patterns for locations in travel itineraries
        patterns = [
            # Specific attraction patterns
            r'(?:visit|go to|explore|see|at|near)\s+([A-Z][a-zA-Z\s-]+(?:Tower|Museum|Palace|Temple|Church|Cathedral|Market|Beach|Square|Bridge|Garden|Gallery|Stadium|Airport|Station|Basilica|Arc|Castle))',
            # Direct attraction names
            r'\b([A-Z][a-zA-Z\s-]+(?:Tower|Museum|Palace|Temple|Church|Cathedral|Market|Beach|Square|Bridge|Garden|Gallery|Stadium|Airport|Station|Basilica|Arc|Castle))\b',
            # Famous landmarks (specific patterns)
            r'\b(Eiffel Tower|Louvre Museum|Notre-Dame Cathedral|Arc de Triomphe|Sacré-Cœur Basilica|Times Square|Central Park|Big Ben|London Eye|Statue of Liberty|Golden Gate Bridge)\b',
            # Street addresses
            r'\b([A-Z][a-zA-Z\s]+(?:Street|Avenue|Road|Boulevard|Lane))\b',
            # Hotels and restaurants
            r'\b([A-Z][a-zA-Z\s]+(?:Restaurant|Café|Hotel|Inn|Lodge))\b'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 3:  # Filter out very short matches
                        clean_match = re.sub(r'^[^a-zA-Z]+', '', match.strip())  # Remove leading non-letters
                        if clean_match:
                            locations.add(clean_match)
        
        return list(locations)
    
    def get_place_suggestions(self, query, limit=10):
        """Get place suggestions from Google Places API"""
        try:
            # Use Google Places API autocomplete
            autocomplete_result = self.gmaps.places_autocomplete(
                input_text=query,
                types=['(cities)'],  # Focus on cities and regions
                language='en'
            )
            
            suggestions = []
            for prediction in autocomplete_result[:limit]:
                suggestion = {
                    'place_id': prediction.get('place_id'),
                    'description': prediction.get('description'),
                    'main_text': prediction.get('structured_formatting', {}).get('main_text', ''),
                    'secondary_text': prediction.get('structured_formatting', {}).get('secondary_text', ''),
                    'types': prediction.get('types', [])
                }
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting place suggestions: {e}")
            return []

# Initialize Google Maps service
gmaps_service = GoogleMapsService()

class AIService:
    """Service class for handling OpenAI GPT interactions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
    
    def _chat_params(self):
        """Return chat parameters for OpenAI API."""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
    
    def get_travel_assistant_prompt(self):
        """Get the system prompt for the travel assistant"""
        return """You are an expert travel assistant AI for Trip-Django, a travel planning platform. Your role is to help users plan amazing trips by providing personalized recommendations, practical advice, and detailed information about destinations worldwide.

Your expertise includes:
- Destination recommendations based on interests, budget, and travel dates
- Travel planning and itinerary creation
- Budget optimization and cost-saving tips
- Cultural insights and local customs
- Transportation options and booking strategies
- Accommodation recommendations
- Food and dining suggestions
- Activities and attractions
- Safety and health considerations
- Visa and documentation requirements
- Weather and seasonal information
- Packing and preparation advice

Guidelines for responses:
1. Always be helpful, enthusiastic, and knowledgeable
2. Ask clarifying questions when needed to provide better recommendations
3. Consider the user's budget, interests, and travel style
4. Provide practical, actionable advice
5. Include specific examples and recommendations when possible
6. Be mindful of safety and current travel conditions
7. Suggest both popular attractions and hidden gems
8. Help optimize their travel experience within their constraints

When users attach files or images:
- For travel documents: Help analyze and provide relevant advice
- For images: Identify locations and provide contextual information
- For itineraries: Review and suggest improvements

Always maintain a friendly, professional tone and focus specifically on travel-related assistance."""

    def generate_optimized_trip_plan(self, trip_request, user=None):
        """Generate a complete, enhanced trip plan in a single OpenAI API call"""
        # Get user context for personalization
        user_context = self.get_user_context(user) if user else ""
        
        # Get any available location data
        location_data = self.get_location_data(trip_request.destination) if trip_request.destination else []
        
        prompt = f"""
You are an expert travel assistant AI. Create a comprehensive, detailed, and enhanced trip plan based on the following user inputs:

TRIP DETAILS:
- Destination: {trip_request.destination}
- Country: {trip_request.destination_country or 'Not specified'}
- Duration: {trip_request.duration} days
- Budget: ${trip_request.budget} total
- Number of travelers: {trip_request.number_of_travelers}
- Interests: {trip_request.interests or 'General exploration'}
- Daily budget: ${trip_request.daily_budget or 'Not specified'}
- Transportation preferences: {trip_request.transportation_preferences or 'Flexible'}
- Experience style: {trip_request.experience_style or 'Balanced'}

USER CONTEXT:
{user_context if user_context else 'No previous travel history available'}

AVAILABLE LOCATION DATA:
{location_data if location_data else 'Use your general knowledge for recommendations'}

CREATE A COMPREHENSIVE PLAN INCLUDING:
1. Detailed day-by-day itinerary with specific locations, attractions, and activities
2. Specific restaurant recommendations with estimated costs (include in budget calculations)
3. Hotel/accommodation recommendations with estimated costs (DO NOT include in trip budget - list separately as additional information for planning purposes)
4. Transportation details and timing recommendations
5. Cultural insights and local tips
6. Hidden gems and local experiences
7. Accurate cost breakdowns for {trip_request.number_of_travelers} travelers (excluding accommodation costs)
8. Daily budget summaries (activities, food, and transportation only)
9. Separate accommodation section with hotel recommendations and estimated costs

IMPORTANT FORMATTING RULES:
- NEVER use hashtags (#), asterisks (*), or other special characters for headers or emphasis
- Always use relevant emojis at the beginning of sections and activities
- Use emojis like 🌟, 🗓️, 📍, 🏨, 🍽️, 🎯, 🚗, 💰, ⏰, 🎨, 🏛️, 🌊, 🎪 etc.
- Make the content visually appealing with appropriate emojis
- Use simple text formatting without markdown symbols
- Include specific location names for photo integration

Format example:
🌟 Amazing Trip to [Destination] Enhanced Plan

🗓️ Day 1: Arrival and First Impressions
- 🚗 Airport Transfer: Details about transportation options and costs
- 🍽️ Lunch at [Specific Restaurant]: Description and cost estimate
- 📍 Visit [Specific Attraction]: Detailed description, opening hours, entry fees
- 💰 Daily total (activities, food, transport): $XX for {trip_request.number_of_travelers} travelers
- ⏰ Timing Tips: Best times and practical advice

🏨 ACCOMMODATION RECOMMENDATIONS (Budget Separately):
- [Specific Hotel Name]: Description, amenities, and estimated cost for {trip_request.number_of_travelers} people per night
- Alternative options with different price ranges

Please provide a rich, detailed itinerary that makes full use of the budget and creates an amazing travel experience.
"""
        messages = [
            {"role": "system", "content": self.get_travel_assistant_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    timeout=120,
                    **self._chat_params()
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                error_message = str(e)
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {error_message}")
                
                if attempt == max_retries - 1:  # Last attempt
                    if "timeout" in error_message.lower() or "timed out" in error_message.lower():
                        logger.error(f"Request timed out after {max_retries} attempts.")
                        raise Exception("Request timed out.")
                    elif "connection" in error_message.lower():
                        logger.error(f"Connection error after {max_retries} attempts.")
                        raise Exception("Connection error.")
                    elif "rate_limit" in error_message.lower() or "quota" in error_message.lower() or "insufficient_quota" in error_message.lower():
                        logger.warning(f"API rate limit or quota exceeded. Will use fallback plan.")
                        raise Exception("API quota exceeded.")
                    else:
                        logger.error(f"Error generating optimized trip plan: {e}")
                        raise Exception(f"Error generating trip plan: {e}")
                
                # Wait before retry (exponential backoff)
                import time
                time.sleep(2 ** attempt)
    
    def generate_trip_plan(self, trip_request):
        """Legacy method - redirect to optimized version"""
        return self.generate_optimized_trip_plan(trip_request)



    def get_user_context(self, user=None):
        """Get user context from database for personalized responses"""
        if not user or not user.is_authenticated:
            return ""
        
        context = []
        
        # Add user preferences
        if user.preferred_budget_range:
            context.append(f"User's preferred budget range: {user.preferred_budget_range}")
        if user.travel_style:
            context.append(f"User's travel style: {user.travel_style}")
        if user.dietary_restrictions:
            context.append(f"User's dietary restrictions: {user.dietary_restrictions}")
        if user.previous_destinations:
            context.append(f"User's previous destinations: {user.previous_destinations}")
        
        # Add trip history
        try:
            
            recent_trips = UserTripHistory.objects.filter(user=user).order_by('-trip_date')[:3]
            if recent_trips:
                trip_info = []
                for trip in recent_trips:
                    rating_text = f" (rated {trip.satisfaction_rating}/5)" if trip.satisfaction_rating else ""
                    trip_info.append(f"{trip.destination.name}{rating_text}")
                context.append(f"User's recent trips: {', '.join(trip_info)}")
        except ImportError:
            pass
        
        return "\n".join(context) if context else ""
    
    def get_location_data(self, destination_name):
        """Get location data with images and schedules from database"""
        try:
            from .models import Destination, Location
            destination = Destination.objects.filter(name__icontains=destination_name).first()
            if destination:
                locations = Location.objects.filter(destination=destination)
                location_data = []
                for loc in locations:
                    data = {
                        'name': loc.name,
                        'description': loc.description,
                        'image_url': loc.image_url,
                        'average_cost': loc.average_cost,
                        'opening_hours': loc.opening_hours,
                        'best_time_to_visit': loc.best_time_to_visit,
                        'category': loc.category
                    }
                    location_data.append(data)
                return location_data
        except ImportError:
            pass
        return []
    
    def generate_enhanced_response(self, initial_plan, user=None, destination=None, number_of_travelers=1):
        """Generate enhanced response with location images, schedules, and costs"""
        try:
            # Get user context
            user_context = self.get_user_context(user)
            
            # Get location data
            location_data = self.get_location_data(destination) if destination else []
            
            # Create enhanced prompt
            prompt = f"""
Based on this initial travel plan:
{initial_plan}

{user_context if user_context else ''}

Please enhance this plan by:
1. Adding specific location details and visual descriptions
2. Including detailed schedules and opening hours where applicable
3. Providing accurate cost estimates for {number_of_travelers} travelers
4. Adding practical tips and local insights
5. Including hidden gems and local recommendations
6. Suggesting optimal timing for each activity
7. Adding daily budget breakdowns

Available location data: {location_data if location_data else 'None available, use general knowledge'}

IMPORTANT FORMATTING RULES:
- NEVER use hashtags (#), asterisks (*), or other special characters for headers or emphasis
- Always use relevant emojis at the beginning of sections and activities
- Use emojis like 🌟, 🗓️, 📍, 🏨, 🍽️, 🎯, 🚗, 💰, ⏰, 🎨, 🏛️, 🌊, 🎪 etc.
- Make the content visually appealing with appropriate emojis
- Use simple text formatting without markdown symbols

Format the response as a comprehensive, enhanced travel itinerary with:
- Day-by-day breakdown
- Cost estimates per activity/meal for {number_of_travelers} people
- Timing recommendations
- Visual descriptions of locations
- Practical travel tips
- Local recommendations
- Daily budget summaries
"""
            
            messages = [
                {"role": "system", "content": self.get_travel_assistant_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                timeout=120,
                **self._chat_params()
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating enhanced response: {e}")
            return initial_plan  # Fallback to initial plan
    
    def generate_response(self, message, file_attachment=None, voice_attachment=None, chat_history=None, user=None):
        """Generate AI response using GPT-4"""
        try:
            messages = [{"role": "system", "content": self.get_travel_assistant_prompt()}]
            
            # Add chat history if provided (last 10 messages for context)
            if chat_history and len(chat_history) > 0:
                # Get the last 10 messages safely
                recent_messages = list(chat_history)[-10:] if len(chat_history) > 10 else list(chat_history)
                for chat_msg in recent_messages:
                    role = "user" if chat_msg.sender == "user" else "assistant"
                    if chat_msg.content:
                        messages.append({"role": role, "content": chat_msg.content})
            
            # Handle file attachments
            user_content = []
            
            if message:
                user_content.append({"type": "text", "text": message})
            
            # Handle image attachments
            if file_attachment and self._is_image(file_attachment):
                try:
                    image_data = self._encode_image(file_attachment)
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                            "detail": "low"
                        }
                    })
                    if not message:
                        user_content.append({
                            "type": "text", 
                            "text": "I've uploaded an image. Can you help me identify this location and provide travel information about it?"
                        })
                except Exception as e:
                    logger.error(f"Error processing image: {e}")
                    return "I had trouble processing your image. Could you try uploading it again?"
            
            # Handle other file attachments
            elif file_attachment:
                file_info = f"User uploaded a file: {file_attachment.name}"
                if not message:
                    user_content.append({
                        "type": "text",
                        "text": f"I've uploaded a file ({file_attachment.name}). Can you help me with travel-related questions about this document?"
                    })
                else:
                    user_content.append({
                        "type": "text",
                        "text": f"{message} (Note: User also uploaded {file_attachment.name})"
                    })
            
            # Handle voice attachments
            elif voice_attachment:
                if not message:
                    user_content.append({
                        "type": "text",
                        "text": "I sent you a voice message about travel planning. How can you help me?"
                    })
            
            # If no content, provide default message
            if not user_content:
                user_content.append({
                    "type": "text",
                    "text": "Hello! I'd like help with travel planning."
                })
            
            messages.append({"role": "user", "content": user_content})
            
            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                **self._chat_params()
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._get_fallback_response(message, file_attachment, voice_attachment)
    
    def _is_image(self, file):
        """Check if uploaded file is an image"""
        if hasattr(file, 'content_type'):
            return file.content_type.startswith('image/')
        elif hasattr(file, 'name'):
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            return any(file.name.lower().endswith(ext) for ext in image_extensions)
        return False
    
    def _encode_image(self, image_file):
        """Encode image to base64 for OpenAI Vision API"""
        try:
            image_file.seek(0)  # Reset file pointer
            image_data = image_file.read()
            return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    def _get_fallback_response(self, message, file_attachment, voice_attachment):
        """Provide fallback response when OpenAI API fails"""
        if file_attachment and self._is_image(file_attachment):
            return "I can see you've shared an image! While I'm having trouble processing it right now, I'd be happy to help you with travel planning. Could you tell me about the destination you're interested in or what specific travel advice you're looking for?"
        
        elif file_attachment:
            return f"I see you've uploaded a file ({file_attachment.name}). I'm here to help with your travel planning! Could you tell me what specific information you're looking for? I can assist with destinations, budgets, itineraries, and much more."
        
        elif voice_attachment:
            return "I received your voice message! I'm your travel planning assistant and I'm here to help with destinations, budgets, itineraries, accommodations, and all aspects of travel. What would you like to know?"
        
        elif message:
            # Simple keyword-based fallback
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['budget', 'money', 'cost', 'price', 'expensive', 'cheap']):
                return "Budget planning is crucial for a great trip! I can help you create a detailed budget breakdown. Consider allocating roughly: 40-50% for accommodation and flights, 20-30% for food, 15-25% for activities, and 10-15% for miscellaneous expenses. What's your target budget and destination?"
            
            elif any(word in message_lower for word in ['destination', 'where', 'place', 'country', 'city', 'visit']):
                return "Choosing the perfect destination is exciting! To give you the best recommendations, I'd love to know: What type of experience are you seeking (adventure, relaxation, culture, nightlife)? What's your budget range? When are you planning to travel? And do you prefer hot or cool climates?"
            
            elif any(word in message_lower for word in ['hotel', 'accommodation', 'stay', 'booking', 'airbnb']):
                return "Great choice focusing on accommodations! Here are some tips: Book 2-3 months ahead for better rates, read recent reviews, check cancellation policies, and consider location vs. price. Hotels offer services, Airbnb offers local experience, and hostels are budget-friendly. What type of accommodation and destination are you considering?"
            
            elif any(word in message_lower for word in ['flight', 'airline', 'plane', 'airport', 'ticket']):
                return "Smart to plan flights early! Here's what I recommend: Book domestic flights 1-3 months ahead, international flights 2-8 months ahead. Tuesday/Wednesday are often cheapest. Use flight comparison tools, consider nearby airports, and be flexible with dates. Where are you planning to fly to and from?"
            
            elif any(word in message_lower for word in ['itinerary', 'plan', 'schedule', 'activities']):
                return "I'd love to help create an amazing itinerary! A good rule is: don't overpack your schedule, mix must-see attractions with local experiences, allow time for spontaneity, and consider travel time between locations. What destination and how many days are you planning?"
            
            else:
                return "Hello! I'm your AI travel assistant, and I'm excited to help you plan an amazing trip! I can assist with destinations, budgets, itineraries, accommodations, flights, activities, and much more. What aspect of travel planning would you like to explore today?"
        
        return "I'm here to help with all your travel planning needs! Whether you're looking for destination ideas, budget advice, itinerary planning, or specific travel tips, just let me know what you'd like to explore!"
    
    def generate_contextual_response(self, message, trip_context, file_attachment=None, chat_history=None, user=None):
        """Generate AI response with trip context for personalized assistance"""
        try:
            # Build context-aware system prompt
            contextual_prompt = f"""
            You are an expert travel assistant AI for Trip-Django. You are currently helping a user with their specific trip request.
            
            TRIP CONTEXT:
            - Destination: {trip_context.get('destination')} ({trip_context.get('country')})
            - Duration: {trip_context.get('duration')} days
            - Budget: ${trip_context.get('budget')}
            - Number of travelers: {trip_context.get('number_of_travelers')}
            - Interests: {trip_context.get('interests', 'Not specified')}
            - Daily budget: ${trip_context.get('daily_budget', 'Not specified')}
            - Transportation preferences: {trip_context.get('transportation_preferences', 'Not specified')}
            - Experience style: {trip_context.get('experience_style', 'Not specified')}
            - Trip request ID: {trip_context.get('trip_id')}
            - Has generated plan: {trip_context.get('has_generated_plan')}
            
            {f"EXISTING PLAN PREVIEW: {trip_context.get('generated_plan_content', '')}" if trip_context.get('has_generated_plan') else ""}
            
            Use this context to provide personalized, specific advice about their trip. You can:
            - Suggest modifications to their existing plan
            - Answer questions about their destination
            - Help optimize their budget and itinerary
            - Provide local insights and tips
            - Assist with booking strategies
            - Address any concerns about their trip
            
            Always reference their specific trip details when relevant and provide actionable advice.
            """
            
            messages = [{"role": "system", "content": contextual_prompt}]
            
            # Add chat history if provided (last 10 messages for context)
            if chat_history and len(chat_history) > 0:
                recent_messages = list(chat_history)[-10:] if len(chat_history) > 10 else list(chat_history)
                for chat_msg in recent_messages:
                    role = "user" if chat_msg.sender == "user" else "assistant"
                    if chat_msg.content:
                        messages.append({"role": role, "content": chat_msg.content})
            
            # Handle user message and attachments
            user_content = []
            
            if message:
                user_content.append({"type": "text", "text": message})
            
            # Handle image attachments
            if file_attachment and self._is_image(file_attachment):
                try:
                    image_data = self._encode_image(file_attachment)
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                            "detail": "low"
                        }
                    })
                    if not message:
                        user_content.append({
                            "type": "text", 
                            "text": "I've uploaded an image related to my trip. Can you help me with this?"
                        })
                except Exception as e:
                    logger.error(f"Error processing image: {e}")
                    return "I had trouble processing your image. Could you try uploading it again?"
            
            # Handle other file attachments
            elif file_attachment:
                if not message:
                    user_content.append({
                        "type": "text",
                        "text": f"I've uploaded a file ({file_attachment.name}) related to my trip. Can you help me with this?"
                    })
                else:
                    user_content.append({
                        "type": "text",
                        "text": f"{message} (Note: I also uploaded {file_attachment.name})"
                    })
            
            # If no content, provide default message
            if not user_content:
                user_content.append({
                    "type": "text",
                    "text": "I need help with my trip planning. Can you assist me?"
                })
            
            messages.append({"role": "user", "content": user_content})
            
            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error in contextual response: {e}")
            return self._get_contextual_fallback_response(message, trip_context)
    
    def _get_contextual_fallback_response(self, message, trip_context):
        """Provide contextual fallback response when OpenAI API fails"""
        destination = trip_context.get('destination', 'your destination')
        duration = trip_context.get('duration', 'your trip')
        
        if message:
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['budget', 'money', 'cost', 'price', 'expensive', 'cheap']):
                return f"I'd love to help you optimize your budget for your {duration}-day trip to {destination}! Based on your current budget of ${trip_context.get('budget')}, I can suggest ways to make the most of your money. What specific aspect of budgeting would you like help with?"
            
            elif any(word in message_lower for word in ['itinerary', 'plan', 'schedule', 'activities', 'what to do']):
                return f"I'm here to help you perfect your itinerary for {destination}! With {duration} days and {trip_context.get('number_of_travelers')} travelers, we can create an amazing experience. What specific activities or aspects of your trip would you like to focus on?"
            
            elif any(word in message_lower for word in ['hotel', 'accommodation', 'stay', 'where to stay']):
                return f"Great question about accommodations in {destination}! For your {duration}-day trip with {trip_context.get('number_of_travelers')} travelers, I can suggest options that fit your budget of ${trip_context.get('budget')}. What type of accommodation experience are you looking for?"
            
            else:
                return f"I'm your travel assistant and I'm here to help with your {duration}-day trip to {destination}! I have all the details about your trip plan and can help you with any questions or modifications. What would you like to know or change about your trip?"
        
        return f"I'm ready to help you with your upcoming trip to {destination}! I have all your trip details and can assist with planning, budgeting, activities, and any questions you might have. How can I help make your {duration}-day trip amazing?"
def generate_trip_plan_pdf(trip_plan_text, destination_city=None):
    """Generate a professional PDF using ReportLab with emoji support, Google Maps links and location photos"""
    try:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=50, rightMargin=50,
                                topMargin=50, bottomMargin=50)
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='TripTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=black,
        ))
        
        # Day header style
        styles.add(ParagraphStyle(
            name='DayHeader',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            spaceAfter=12,
            spaceBefore=20,
            textColor=black,
            leftIndent=0,
        ))
        
        # Activity style
        styles.add(ParagraphStyle(
            name='Activity',
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            spaceAfter=8,
            leftIndent=20,
            bulletIndent=10,
        ))
        
        # Sub-activity style
        styles.add(ParagraphStyle(
            name='SubActivity',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            spaceAfter=6,
            leftIndent=40,
            bulletIndent=30,
            textColor=black,
        ))
        
        # Cost information style
        styles.add(ParagraphStyle(
            name='CostInfo',
            fontName='Helvetica-Oblique',
            fontSize=10,
            leading=13,
            spaceAfter=6,
            leftIndent=30,
            textColor=blue,
        ))
        
        # Tips style
        styles.add(ParagraphStyle(
            name='TipStyle',
            fontName='Helvetica-Oblique',
            fontSize=10,
            leading=13,
            spaceAfter=8,
            leftIndent=20,
            textColor=black,
        ))
        
        story = []
        
        # Extract locations from the text for Google Maps links and photos
        locations = gmaps_service.extract_locations_from_text(trip_plan_text)
        logger.info(f"Extracted {len(locations)} locations: {locations}")
        
        # Pre-fetch location details to avoid duplicates
        location_details = {}
        for location in locations:
            try:
                place_details = gmaps_service.get_place_details(location, destination_city)
                if place_details:
                    location_details[location] = place_details
                    logger.info(f"Found {len(place_details.get('photos', []))} photos for {location}")
                else:
                    logger.warning(f"No place details found for {location}")
            except Exception as e:
                logger.error(f"Error getting place details for {location}: {e}")
                location_details[location] = None
        
        # Process the content
        lines = trip_plan_text.split('\n')
        
        for i, line in enumerate(lines):
            if not line.strip():
                story.append(Spacer(1, 8))
                continue
                
            # Clean the line and escape HTML characters
            cleaned_line = html.escape(line.strip())
            
            # Determine line type and apply appropriate formatting
            style_name = 'Activity'  # Default style
            
            # Check for different content types based on emojis and keywords
            if i == 0 and len(lines) > 1:  # First line might be title
                style_name = 'TripTitle'
            elif re.match(r'^(.*Day \d+|.*🗓️)', cleaned_line, re.IGNORECASE):
                style_name = 'DayHeader'
            elif re.match(r'^(.*💰|.*Cost|.*Price|.*Budget)', cleaned_line, re.IGNORECASE):
                style_name = 'CostInfo'
            elif re.match(r'^(.*💡|.*⚠️|.*Tip|.*Note|.*Info)', cleaned_line, re.IGNORECASE):
                style_name = 'TipStyle'
            elif re.match(r'^\s*[-•]', cleaned_line) or line.startswith('  '):
                style_name = 'SubActivity'
            
            # Process line for location links
            line_with_links = cleaned_line
            
            # Find locations in this line and add Google Maps links
            for location in locations:
                if location.lower() in line_with_links.lower():
                    # Generate Google Maps link
                    maps_link = gmaps_service.generate_google_maps_link(location, destination_city)
                    
                    # Replace location name with a hyperlink (escape the location name)
                    escaped_location = html.escape(location)
                    location_pattern = re.compile(re.escape(escaped_location), re.IGNORECASE)
                    line_with_links = location_pattern.sub(
                        f'<a href="{maps_link}" color="blue">{escaped_location}</a>',
                        line_with_links,
                        count=1
                    )
            
            # Handle special formatting for headers
            if style_name in ['DayHeader', 'TripTitle']:
                if not line_with_links.startswith('<b>'):
                    line_with_links = f'<b>{line_with_links}</b>'
            
            # Add bullet points for activities if not already present and not a special line
            if style_name == 'Activity' and not re.match(r'^[🏨🍽️🎯🚗📍⏰🎨🏛️🌊🎪•\-]', line_with_links):
                if not line_with_links.startswith('<b>'):
                    line_with_links = f'• {line_with_links}'
            
            # Create paragraph with appropriate style
            try:
                story.append(Paragraph(line_with_links, styles[style_name]))
            except Exception as e:
                # Fallback to default style if there's an issue
                logger.warning(f"Error formatting line '{cleaned_line}': {e}")
                story.append(Paragraph(line_with_links, styles['Activity']))
        
        # Add photos section for locations with images
        photos_added = set()  # Track which locations we've added photos for
        
        if any(details and details.get('photos') for details in location_details.values()):
            story.append(Spacer(1, 30))
            story.append(Paragraph('📸 Location Photos', styles['DayHeader']))
            story.append(Spacer(1, 15))
            
            for location, details in location_details.items():
                if details and details.get('photos') and location not in photos_added:
                    try:
                        # Add location name
                        location_header = f'📍 {details.get("name", location)}'
                        if details.get('rating'):
                            location_header += f' ⭐ {details["rating"]}'
                        story.append(Paragraph(location_header, styles['SubActivity']))
                        
                        # Create table for photos (up to 3 per row)
                        photos = details['photos'][:3]  # Limit to 3 photos
                        photo_data = []
                        
                        for photo_info in photos:
                            try:
                                # Fetch image from Google
                                logger.info(f"Fetching image from URL: {photo_info['url']}")
                                response = urllib.request.urlopen(photo_info['url'], timeout=10)
                                img_data = response.read()
                                
                                # Create ReportLab Image object
                                img_buffer = io.BytesIO(img_data)
                                img = Image(img_buffer, width=1.8*inch, height=1.2*inch)
                                photo_data.append(img)
                                logger.info(f"Successfully added image for {location}")
                                
                            except Exception as img_error:
                                logger.warning(f"Failed to fetch/process image for {location}: {img_error}")
                                # Add placeholder text instead of image
                                photo_data.append(Paragraph(f'📷 Photo unavailable', styles['SubActivity']))
                        
                        # Add photos to story
                        if photo_data:
                            # Create a table with photos in a single row
                            if len(photo_data) == 1:
                                photo_table_data = [photo_data]
                            else:
                                photo_table_data = [photo_data]  # All in one row
                            
                            photo_table = Table(photo_table_data, colWidths=[1.8*inch] * len(photo_data))
                            photo_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                ('TOPPADDING', (0, 0), (-1, -1), 6),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ]))
                            
                            story.append(photo_table)
                            story.append(Spacer(1, 15))
                            
                        photos_added.add(location)
                        
                    except Exception as location_error:
                        logger.error(f"Error adding photos for {location}: {location_error}")
                        story.append(Paragraph(f'📷 Photos unavailable for {location}', styles['SubActivity']))
                        story.append(Spacer(1, 10))
        
        # Add separator before footer
        story.append(Spacer(1, 30))
        
        # Add footer
        footer_style = ParagraphStyle(
            name='Footer',
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=blue,
            alignment=1,  # Center alignment
        )
        
        footer_text = """<b>🗺️ Interactive Maps:</b> Location names in this itinerary are linked to Google Maps. 
        Click on any location name to view it on the map and get directions.<br/><br/>
        Generated on {} • Trip-Django Travel Planner""".format(datetime.now().strftime('%B %d, %Y'))
        
        story.append(Paragraph(footer_text, footer_style))
        
        doc.build(story)
        buffer.seek(0)
        return ContentFile(buffer.read(), 'trip_plan.pdf')
        
    except Exception as e:
        logger.error(f"Error generating PDF with ReportLab: {e}")
        # Fallback: create a simple text file
        return _generate_fallback_text_file(trip_plan_text, destination_city)

def _generate_fallback_text_file(trip_plan_text, destination_city=None):
    """Generate a simple text file as fallback when PDF generation fails"""
    try:
        # Create a nicely formatted text version
        formatted_text = f"""Trip Plan for {destination_city or 'Your Destination'}
{"=" * 50}

Generated on {datetime.now().strftime('%B %d, %Y')}
Trip-Django Travel Planner

{"=" * 50}

{trip_plan_text}

{"=" * 50}

Note: Location names would be linked to Google Maps in the PDF version.
For the best experience, please try generating the PDF again.
"""
        
        return ContentFile(formatted_text.encode('utf-8'), 'trip_plan.txt')
        
    except Exception as e:
        logger.error(f"Fallback text generation also failed: {e}")
        # Last resort: return basic text file
        return ContentFile(trip_plan_text.encode('utf-8'), 'trip_plan.txt')
def generate_enhanced_fallback_plan(trip_request):
    """Generate an enhanced fallback plan with destination-specific recommendations"""
    destination = trip_request.destination
    duration = trip_request.duration
    travelers = trip_request.number_of_travelers
    budget = trip_request.budget
    interests = trip_request.interests or "general exploration"
    
    # Basic destination-specific content
    destination_guides = {
        "london": {
            "highlights": ["Big Ben", "Tower Bridge", "British Museum", "Hyde Park", "Buckingham Palace"],
            "food": ["Fish and chips", "Sunday roast", "Afternoon tea", "Pub food"],
            "transport": "Use the London Underground (Tube) - get an Oyster Card",
            "budget_tip": "Many museums are free. Book theatre shows in advance."
        },
        "paris": {
            "highlights": ["Eiffel Tower", "Louvre Museum", "Notre-Dame", "Champs-Élysées", "Montmartre"],
            "food": ["Croissants", "French pastries", "Bistro meals", "Wine tasting"],
            "transport": "Metro system is efficient - buy day passes",
            "budget_tip": "Visit during happy hour, picnic in parks"
        },
        "tokyo": {
            "highlights": ["Senso-ji Temple", "Shibuya Crossing", "Tokyo Tower", "Meiji Shrine", "Akihabara"],
            "food": ["Sushi", "Ramen", "Tempura", "Street food"],
            "transport": "JR Pass for trains, IC cards for local transport",
            "budget_tip": "Convenience store meals, free temple visits"
        },
        "rome": {
            "highlights": ["Colosseum", "Vatican City", "Trevi Fountain", "Roman Forum", "Pantheon"],
            "food": ["Pizza", "Pasta", "Gelato", "Espresso"],
            "transport": "Walking is best, metro for longer distances",
            "budget_tip": "Free churches, aperitivo culture"
        },
        "barcelona": {
            "highlights": ["Sagrada Familia", "Park Güell", "La Rambla", "Gothic Quarter", "Beach"],
            "food": ["Tapas", "Paella", "Sangria", "Jamón"],
            "transport": "Metro and walking, rent bikes",
            "budget_tip": "Free museums on Sundays, beach days"
        }
    }
    
    # Try to match destination
    dest_key = None
    for key in destination_guides.keys():
        if key.lower() in destination.lower():
            dest_key = key
            break
    
    if dest_key:
        guide = destination_guides[dest_key]
        highlights = ", ".join(guide["highlights"][:3])
        food_items = ", ".join(guide["food"][:3])
        transport_tip = guide["transport"]
        budget_tip = guide["budget_tip"]
    else:
        highlights = "major landmarks and attractions"
        food_items = "local cuisine and specialties"
        transport_tip = "Research local transportation options"
        budget_tip = "Look for free activities and local deals"
    
    # Calculate daily budget
    daily_budget = float(budget) / duration / travelers
    
    return f"""
🌟 Travel Guide for {destination}

📍 Your Trip Overview:
• Destination: {destination}
• Duration: {duration} days
• Travelers: {travelers}
• Total Budget: ${budget}
• Daily Budget per Person: ${daily_budget:.0f}
• Your Interests: {interests}

🗓️ Day-by-Day Framework:

Day 1: Arrival & First Impressions
• 🏨 Check into accommodation (budget: ${daily_budget*0.4:.0f}/person)
• 🍽️ Welcome lunch - try {food_items.split(', ')[0] if ',' in food_items else 'local cuisine'}
• 📍 Visit {highlights.split(', ')[0] if ',' in highlights else 'main attraction'}
• 🚶 Evening stroll and orientation walk
• 💰 Daily estimate: ${daily_budget:.0f} per person

{f'''Day 2: Main Attractions
• 🌅 Early start to {highlights.split(', ')[1] if len(highlights.split(', ')) > 1 else 'popular sites'}
• 🍽️ Lunch featuring {food_items.split(', ')[1] if len(food_items.split(', ')) > 1 else 'regional dishes'}
• 📱 Afternoon at {highlights.split(', ')[2] if len(highlights.split(', ')) > 2 else 'cultural sites'}
• 🌆 Evening entertainment
• 💰 Daily estimate: ${daily_budget:.0f} per person''' if duration >= 2 else ''}

{f'''Day 3: Cultural Immersion
• 🏛️ Museum or cultural site visit
• 🥘 Cooking class or food tour
• 🛍️ Shopping and souvenir hunting
• 📸 Photo opportunities at scenic spots
• 💰 Daily estimate: ${daily_budget:.0f} per person''' if duration >= 3 else ''}

{f'''Day {duration}: Departure
• 🧳 Final shopping or relaxation
• 🍽️ Farewell meal
• 🚗 Airport/station transfer
• ✈️ Safe travels home!''' if duration > 1 else ''}

💡 Essential Tips:
• 🚌 Transportation: {transport_tip}
• 💰 Budget Hack: {budget_tip}
• 📱 Download offline maps and translation apps
• 💳 Notify banks of travel plans
• 🌦 Pack weather-appropriate clothing

🍽️ Must-Try Foods:
{chr(10).join([f'• {food}' for food in food_items.split(', ')])}

📍 Top Attractions:
{chr(10).join([f'• {attraction}' for attraction in highlights.split(', ')])}

🏨 Accommodation Tips:
• Book central locations to save on transport
• Check cancellation policies
• Read recent reviews
• Consider alternative accommodations (Airbnb, hostels)

💳 Budget Breakdown (per person, per day):
• Accommodation: ${daily_budget*0.4:.0f} (40%)
• Food: ${daily_budget*0.3:.0f} (30%)
• Activities: ${daily_budget*0.2:.0f} (20%)
• Transport/Misc: ${daily_budget*0.1:.0f} (10%)

📞 Before You Go:
• Research visa requirements
• Check weather forecasts
• Book popular attractions in advance
• Learn basic local phrases
• Purchase travel insurance

🌐 This enhanced guide was generated to help you plan an amazing trip to {destination}! For real-time information and bookings, consult current travel resources.
"""

# Create a singleton instance
ai_service = AIService()
