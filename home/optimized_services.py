import os
import base64
import json
import hashlib
from django.conf import settings
from django.core.cache import cache
from openai import OpenAI
import logging
import io
import re
import urllib.parse
import urllib.request
import googlemaps
from django.core.files.base import ContentFile
from .models import UserTripHistory
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, blue, grey
from reportlab.lib.units import inch, cm
from datetime import datetime, timedelta
import html

logger = logging.getLogger(__name__)

class CostOptimizedGoogleMapsService:
    """Cost-optimized Google Maps service with intelligent caching"""
    
    def __init__(self):
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        self.cache_timeout = 86400 * 7  # Cache for 7 days
    
    def _get_cache_key(self, operation, *args):
        """Generate cache key for operations"""
        key_data = f"{operation}:{':'.join(str(arg) for arg in args)}"
        return f"gmaps_{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def get_place_details_cached(self, location_name, destination_city=None):
        """Get place details with intelligent caching"""
        cache_key = self._get_cache_key("place_details", location_name, destination_city or "")
        
        # Try cache first
        cached_result = cache.get(cache_key)
        from .cost_monitor import cost_monitor
        
        if cached_result:
            logger.info(f"Cache HIT for place details: {location_name}")
            cost_monitor.track_cache_hit()
            return cached_result
        
        # Check cost limits
        if not cost_monitor.should_allow_api_call('google_maps'):
            logger.warning(f"API limit reached, skipping place details for {location_name}")
            return None
        
        logger.info(f"Cache MISS for place details: {location_name} - Making API call")
        cost_monitor.track_cache_miss()
        
        try:
            # Make API call
            query = location_name
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
                
                # Get photos only for important locations (limit API calls)
                if place.get('place_id') and self._is_important_location(location_name):
                    try:
                        # Use basic place call without specific fields to get all data
                        detailed_place = self.gmaps.place(
                            place_id=place['place_id']
                        )
                        
                        # Check both possible field names
                        photos_data = None
                        if 'photos' in detailed_place['result']:
                            photos_data = detailed_place['result']['photos']
                            logger.info(f"Found 'photos' field with {len(photos_data)} photos")
                        
                        if photos_data:
                            # Only get first photo to reduce costs
                            photo = photos_data[0]
                            photo_reference = photo.get('photo_reference')
                            if photo_reference:
                                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={settings.GOOGLE_MAPS_API_KEY}"
                                place_details['photos'].append({
                                    'url': photo_url,
                                    'width': photo.get('width', 400),
                                    'height': photo.get('height', 300),
                                })
                                logger.info(f"Added photo URL for {location_name}")
                                
                    except Exception as e:
                        logger.warning(f"Error fetching photos for {location_name}: {e}")
                
                # Cache the result
                cache.set(cache_key, place_details, self.cache_timeout)
                return place_details
                
        except Exception as e:
            logger.error(f"Error getting place details for {location_name}: {e}")
        
        # Cache negative result to avoid repeated failed calls
        cache.set(cache_key, None, 3600)  # Cache for 1 hour
        return None
    
    def _is_important_location(self, location_name):
        """Determine if location is important enough to fetch photos"""
        important_keywords = [
            'museum', 'palace', 'temple', 'church', 'cathedral', 'tower', 
            'bridge', 'park', 'square', 'market', 'beach', 'gallery'
        ]
        return any(keyword in location_name.lower() for keyword in important_keywords)
    
    def generate_google_maps_link_simple(self, location_name, destination_city=None):
        """Generate simple Google Maps link without API call"""
        query = f"{location_name}"
        if destination_city:
            query += f", {destination_city}"
        encoded_query = urllib.parse.quote(query)
        return f"https://maps.google.com/?q={encoded_query}"
    
    def get_autocomplete_cached(self, query, limit=5):
        """Get autocomplete suggestions with caching"""
        cache_key = self._get_cache_key("autocomplete", query, limit)
        
        cached_result = cache.get(cache_key)
        from .cost_monitor import cost_monitor

        if cached_result:
            cost_monitor.track_cache_hit()
            return cached_result
        
        cost_monitor.track_cache_miss()
        
        try:
            autocomplete_result = self.gmaps.places_autocomplete(
                input_text=query,
                types=['(cities)'],
                language='en'
            )
            
            suggestions = []
            for prediction in autocomplete_result[:limit]:
                suggestion = {
                    'place_id': prediction.get('place_id'),
                    'description': prediction.get('description'),
                    'main_text': prediction.get('structured_formatting', {}).get('main_text', ''),
                    'secondary_text': prediction.get('structured_formatting', {}).get('secondary_text', ''),
                }
                suggestions.append(suggestion)
            
            # Cache for 24 hours
            cache.set(cache_key, suggestions, 86400)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting autocomplete: {e}")
            return []

class CostOptimizedAIService:
    """Cost-optimized AI service with smart caching and reduced tokens"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-5"  # Upgraded model for better responses
        self.max_tokens = 2500  # Reduced tokens
        self.temperature = 1.0  # gpt-5 uses default temperature
        self.cache_timeout = 86400 * 3  # Cache for 3 days
    
    def _get_cache_key(self, operation, *args):
        """Generate cache key for AI operations"""
        key_data = f"{operation}:{':'.join(str(arg) for arg in args)}"
        return f"ai_{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def generate_optimized_trip_plan_cached(self, trip_request, user=None):
        """Generate trip plan with caching to avoid repeated costs"""
        # Create cache key based on trip parameters
        cache_key_data = [
            trip_request.destination,
            trip_request.destination_country or "",
            str(trip_request.duration),
            str(trip_request.budget),
            str(trip_request.number_of_travelers),
            trip_request.interests or "",
            trip_request.transportation_preferences or "",
            trip_request.experience_style or ""
        ]
        
        cache_key = self._get_cache_key("trip_plan", *cache_key_data)
        
        # Try cache first
        cached_result = cache.get(cache_key)
        from .cost_monitor import cost_monitor

        if cached_result:
            logger.info(f"Cache HIT for trip plan: {trip_request.destination}")
            cost_monitor.track_cache_hit()
            return cached_result
        
        cost_monitor.track_cache_miss()
        
        logger.info(f"Cache MISS for trip plan: {trip_request.destination} - Making API call")
        
        # Use cost-optimized prompt (shorter, more focused)
        prompt = f"""Create a {trip_request.duration}-day trip plan for {trip_request.destination}.

Budget: ${trip_request.budget} for {trip_request.number_of_travelers} travelers
Interests: {trip_request.interests or 'General tourism'}

Format with emojis (NO markdown symbols):
🌟 Trip to {trip_request.destination}

🗓️ Day 1: [Activities]
🏨 Hotel: [Name and cost estimate]
🍽️ Meals: [Restaurant suggestions with costs]
📍 Activities: [Specific locations with timing]
💰 Daily cost: $[amount] per person

Continue for all {trip_request.duration} days.

Include:
- Specific restaurant/hotel names
- Activity costs
- Transportation tips
- Daily budget breakdown
- Local tips

Keep concise but informative."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a travel planning expert. Create detailed, budget-conscious itineraries."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.max_tokens,
                timeout=60
            )
            
            result = response.choices[0].message.content.strip()
            
            # Cache the result
            cache.set(cache_key, result, self.cache_timeout)
            logger.info(f"Generated and cached trip plan for {trip_request.destination}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating trip plan: {e}")
            return self._generate_template_plan(trip_request)
    
    def _generate_template_plan(self, trip_request):
        """Generate a template-based plan as fallback"""
        daily_budget = float(trip_request.budget) / trip_request.duration / trip_request.number_of_travelers
        
        return f"""🌟 {trip_request.destination} Travel Plan

🗓️ Day 1: Arrival & Exploration
🏨 Check-in: Mid-range hotel (${daily_budget * 0.4:.0f}/person)
🍽️ Lunch: Local restaurant (${daily_budget * 0.15:.0f}/person)
📍 Main attraction visit
🍽️ Dinner: Traditional cuisine (${daily_budget * 0.2:.0f}/person)
💰 Daily total: ${daily_budget:.0f} per person

🗓️ Day 2: Cultural Immersion
🏛️ Museum or cultural site
🍽️ Local food tour
🛍️ Shopping district
💰 Daily total: ${daily_budget:.0f} per person

💡 Budget Tips:
- Use public transportation
- Try street food
- Visit free attractions
- Book in advance for discounts"""

# Create optimized instances
optimized_gmaps_service = CostOptimizedGoogleMapsService()
optimized_ai_service = CostOptimizedAIService()

def generate_clean_pdf(trip_plan_text, destination_city=None):
    """Generate enhanced PDF with proper formatting, colors, and location images"""
    try:
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            leftMargin=2*cm, 
            rightMargin=2*cm,
            topMargin=2*cm, 
            bottomMargin=2*cm
        )
        
        # Enhanced professional styles
        styles = getSampleStyleSheet()
        
        # Custom enhanced styles with colors
        title_style = ParagraphStyle(
            name='EnhancedTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            spaceBefore=20,
            alignment=1,  # Center
            textColor=colors.Color(0.2, 0.3, 0.7),  # Blue color
            fontName='Helvetica-Bold',
            backColor=colors.Color(0.95, 0.97, 1.0),  # Light blue background
            borderPadding=15,
            borderRadius=8
        )
        
        day_heading_style = ParagraphStyle(
            name='DayHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=25,
            textColor=colors.Color(0.1, 0.5, 0.3),  # Green color
            fontName='Helvetica-Bold',
            backColor=colors.Color(0.95, 1.0, 0.95),  # Light green background
            borderPadding=12,
            leftIndent=10
        )
        
        activity_style = ParagraphStyle(
            name='Activity',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=25,
            fontName='Helvetica',
            textColor=colors.black
        )
        
        cost_style = ParagraphStyle(
            name='CostInfo',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=25,
            fontName='Helvetica-Bold',
            textColor=colors.Color(0.8, 0.4, 0.1),  # Orange for costs
            backColor=colors.Color(1.0, 0.98, 0.9)  # Light orange background
        )
        
        tip_style = ParagraphStyle(
            name='TipStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            leftIndent=25,
            fontName='Helvetica-Oblique',
            textColor=colors.Color(0.4, 0.4, 0.6),  # Purple for tips
            backColor=colors.Color(0.98, 0.98, 1.0)  # Light purple background
        )
        
        # Extract locations for image fetching
        locations = extract_locations_from_text(trip_plan_text)
        logger.info(f"Extracted {len(locations)} locations for PDF: {locations}")
        
        # Fetch location details for images
        location_details = {}
        for location in locations[:5]:  # Limit to 5 locations to control costs
            try:
                place_details = optimized_gmaps_service.get_place_details_cached(location, destination_city)
                if place_details and place_details.get('photos'):
                    location_details[location] = place_details
                    logger.info(f"Found location details with {len(place_details.get('photos', []))} photos for {location}")
            except Exception as e:
                logger.warning(f"Error fetching details for {location}: {e}")
        
        # Build content
        story = []
        lines = trip_plan_text.split('\n')
        
        # Define a regex to strip emojis
        emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 8))
                continue
            
            # Clean the line from emojis and escape HTML characters
            cleaned_line = emoji_pattern.sub(r'', html.escape(line))
            
            # Determine style based on content
            if i == 0 or (i < 3 and "Travel Plan" in cleaned_line):
                story.append(Paragraph(cleaned_line, title_style))
            elif cleaned_line.startswith("Day ") or cleaned_line.startswith("🗓️"):
                story.append(Paragraph(cleaned_line.replace("🗓️", "").strip(), day_heading_style))
            elif "cost" in cleaned_line.lower() or "$" in cleaned_line:
                story.append(Paragraph(cleaned_line, cost_style))
            elif "tip" in cleaned_line.lower() or "note" in cleaned_line.lower():
                story.append(Paragraph(cleaned_line, tip_style))
            else:
                # Process normal content with location links
                line_with_links = cleaned_line
                
                # More comprehensive location patterns
                location_patterns = [
                    r'\b([A-Z][a-zA-Z\s]+(?:Museum|Palace|Temple|Church|Cathedral|Tower|Bridge|Park|Square|Market|Gallery|Beach|Airport|Station|Restaurant|Café|Hotel))\b'
                ]
                
                for pattern in location_patterns:
                    matches = re.finditer(pattern, line_with_links)
                    for match in matches:
                        location = match.group(1)
                        maps_url = f"https://maps.google.com/?q={urllib.parse.quote(location + ', ' + (destination_city or ''))}"
                        line_with_links = line_with_links.replace(
                            location, 
                            f'<a href="{maps_url}" color="blue"><u>{location}</u></a>', 
                            1
                        )
                
                story.append(Paragraph(line_with_links, activity_style))
        
        # Add location images section if we have any
        if location_details:
            story.append(Spacer(1, 30))
            
            # Section header for photos
            photo_header_style = ParagraphStyle(
                name='PhotoHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.Color(0.2, 0.3, 0.7),
                fontName='Helvetica-Bold',
                backColor=colors.Color(0.95, 0.97, 1.0),
                borderPadding=10
            )
            
            story.append(Paragraph('Destination Photos', photo_header_style))
            story.append(Spacer(1, 15))
            
            for location, details in location_details.items():
                if details and details.get('photos'):
                    try:
                        # Location name
                        location_name = details.get('name', location)
                        rating_text = f" - Rating: {details['rating']}/5" if details.get('rating') else ""
                        
                        location_header_style = ParagraphStyle(
                            name='LocationHeader',
                            parent=styles['Normal'],
                            fontSize=12,
                            spaceAfter=10,
                            fontName='Helvetica-Bold',
                            textColor=colors.Color(0.1, 0.5, 0.3)
                        )
                        
                        story.append(Paragraph(f"{location_name}{rating_text}", location_header_style))
                        
                        # Try to add photos
                        photos = details['photos'][:2]  # Limit to 2 photos per location
                        photo_elements = []
                        
                        for photo_info in photos:
                            try:
                                logger.info(f"Fetching photo: {photo_info['url']}")
                                response = urllib.request.urlopen(photo_info['url'], timeout=15)
                                img_data = response.read()
                                
                                # Create image
                                img_buffer = io.BytesIO(img_data)
                                img = Image(img_buffer, width=4*cm, height=3*cm)
                                photo_elements.append(img)
                                
                                logger.info(f"Successfully added photo for {location}")
                                
                            except Exception as img_error:
                                logger.warning(f"Failed to fetch image for {location}: {img_error}")
                                # Add placeholder text
                                placeholder_style = ParagraphStyle(
                                    name='PhotoPlaceholder',
                                    parent=styles['Normal'],
                                    fontSize=9,
                                    textColor=colors.grey,
                                    alignment=1
                                )
                                photo_elements.append(Paragraph(f"Photo unavailable for {location}", placeholder_style))
                        
                        # Add photos to story
                        if photo_elements:
                            if len(photo_elements) == 1:
                                story.append(photo_elements[0])
                            else:
                                # Create table for multiple photos
                                photo_table = Table([photo_elements], colWidths=[4*cm] * len(photo_elements))
                                photo_table.setStyle(TableStyle([
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                                ]))
                                story.append(photo_table)
                            
                            story.append(Spacer(1, 15))
                        
                    except Exception as location_error:
                        logger.error(f"Error processing location {location}: {location_error}")
        
        # Add enhanced footer with styling
        story.append(Spacer(1, 40))
        
        footer_style = ParagraphStyle(
            name='EnhancedFooter',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,  # Center
            textColor=colors.Color(0.4, 0.4, 0.4),
            fontName='Helvetica-Oblique',
            backColor=colors.Color(0.98, 0.98, 0.98),
            borderPadding=10
        )
        
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y')} • TripAI Travel Planner • Professional Trip Planning Service"
        story.append(Paragraph(footer_text, footer_style))
        
        doc.build(story)
        buffer.seek(0)
        return ContentFile(buffer.read(), 'trip_plan.pdf')
        
    except Exception as e:
        logger.error(f"Error generating enhanced PDF: {e}")
        # Return text file as fallback
        return ContentFile(trip_plan_text.encode('utf-8'), 'trip_plan.txt')

def cost_optimized_trip_generation(trip_request_id, user_id):
    """Highly optimized trip generation with minimal API costs"""
    try:
        from .models import TripPlanRequest, GeneratedPlan
        
        trip_request = TripPlanRequest.objects.get(id=trip_request_id)
        
        # Check if plan already exists
        try:
            existing_plan = trip_request.generated_plan
            if existing_plan.content and len(existing_plan.content.strip()) > 100:
                logger.info(f"Trip plan already exists for {trip_request_id}")
                # Generate PDF if missing
                if not existing_plan.pdf_file:
                    logger.info(f"Generating missing PDF for existing plan {trip_request_id}")
                    pdf_content = generate_clean_pdf(existing_plan.content, trip_request.destination)
                    existing_plan.pdf_file.save(f"trip_plan_{trip_request_id}.pdf", pdf_content)
                    existing_plan.save()
                return
        except GeneratedPlan.DoesNotExist:
            pass
        
        # Generate new plan with cost optimization
        logger.info(f"Generating cost-optimized trip plan for {trip_request_id}")
        
        try:
            # Use cached AI service
            trip_content = optimized_ai_service.generate_optimized_trip_plan_cached(trip_request)
            
            # Generate clean PDF immediately
            pdf_content = generate_clean_pdf(trip_content, trip_request.destination)
            
            # Save plan and PDF in one operation
            plan, created = GeneratedPlan.objects.get_or_create(
                trip_request=trip_request,
                defaults={'content': trip_content}
            )
            
            plan.content = trip_content
            plan.pdf_file.save(f"trip_plan_{trip_request_id}.pdf", pdf_content)
            plan.save()
            
            logger.info(f"✅ Cost-optimized plan generated for {trip_request_id}")
            
        except Exception as e:
            logger.error(f"Error in cost-optimized generation: {e}")
            # Use template fallback
            fallback_content = generate_template_fallback(trip_request)
            
            plan, created = GeneratedPlan.objects.get_or_create(
                trip_request=trip_request,
                defaults={'content': fallback_content}
            )
            
            plan.content = fallback_content
            pdf_content = generate_clean_pdf(fallback_content, trip_request.destination)
            plan.pdf_file.save(f"trip_plan_{trip_request_id}.pdf", pdf_content)
            plan.save()
            
    except Exception as e:
        logger.error(f"Error in cost_optimized_trip_generation: {e}")

def generate_template_fallback(trip_request):
    """Generate a high-quality template-based plan without API calls"""
    dest = trip_request.destination
    days = trip_request.duration
    travelers = trip_request.number_of_travelers
    budget = float(trip_request.budget)
    daily_budget = budget / days / travelers
    
    # Popular destinations template data
    dest_data = {
        'paris': {
            'attractions': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame Cathedral', 'Arc de Triomphe', 'Sacré-Cœur Basilica'],
            'food': ['French bistro', 'Café de Flore', 'Local boulangerie', 'Seine-side restaurant'],
            'transport': 'Metro day pass (€7.50/day)',
            'tips': 'Many museums free first Sunday of month'
        },
        'london': {
            'attractions': ['Big Ben', 'Tower Bridge', 'British Museum', 'Hyde Park', 'Buckingham Palace'],
            'food': ['Traditional pub', 'Borough Market', 'Fish and chips shop', 'Afternoon tea'],
            'transport': 'Oyster Card for Tube (£15/day)',
            'tips': 'Most museums are free entry'
        },
        'rome': {
            'attractions': ['Colosseum', 'Vatican City', 'Trevi Fountain', 'Roman Forum', 'Pantheon'],
            'food': ['Trattoria', 'Gelato shop', 'Roman pizzeria', 'Osteria'],
            'transport': 'Roma Pass (€38.50/3 days)',
            'tips': 'Churches are free, avoid tourist traps near landmarks'
        }
    }
    
    # Get data for destination
    key = None
    for k in dest_data.keys():
        if k.lower() in dest.lower():
            key = k
            break
    
    if key:
        data = dest_data[key]
        attractions = data['attractions'][:days]  # Match attractions to days
        restaurants = data['food']
        transport_info = data['transport']
        budget_tip = data['tips']
    else:
        attractions = ['Main attraction', 'Cultural site', 'Historic landmark', 'Local market', 'Scenic viewpoint'][:days]
        restaurants = ['Local restaurant', 'Traditional eatery', 'Popular café', 'Street food vendor']
        transport_info = 'Research local transport options'
        budget_tip = 'Look for free activities and local deals'
    
    plan = f"🌟 {dest} Travel Plan\n\n"
    
    for day in range(1, days + 1):
        plan += f"🗓️ Day {day}: "
        if day == 1:
            plan += "Arrival & First Impressions\n"
        elif day == days:
            plan += "Final Day & Departure\n"
        else:
            plan += f"Exploring {dest}\n"
        
        plan += f"🏨 Accommodation: Budget hotel (${daily_budget * 0.35:.0f}/person)\n"
        
        if day <= len(attractions):
            plan += f"📍 Visit: {attractions[day-1]}\n"
        
        if day <= len(restaurants):
            plan += f"🍽️ Lunch: {restaurants[(day-1) % len(restaurants)]} (${daily_budget * 0.15:.0f}/person)\n"
        
        plan += f"🚶 Evening: Local exploration\n"
        plan += f"💰 Daily total: ${daily_budget:.0f} per person\n\n"
    
    plan += f"🚌 Transportation: {transport_info}\n"
    plan += f"💡 Budget Tip: {budget_tip}\n"
    
    return plan

def extract_locations_from_text(text):
    """Extract potential location names from text using regex patterns"""
    lines = text.split('\n')
    locations = set()
    
    # Enhanced patterns for locations in travel itineraries
    patterns = [
        # Specific attraction patterns
        r'(?:visit|go to|explore|see|at|near)\s+([A-Z][a-zA-Z\s-]+(?:Tower|Museum|Palace|Temple|Church|Cathedral|Market|Beach|Square|Bridge|Garden|Gallery|Stadium|Airport|Station|Basilica|Arc|Castle|Restaurant|Café|Hotel))',
        # Direct attraction names
        r'\b([A-Z][a-zA-Z\s-]+(?:Tower|Museum|Palace|Temple|Church|Cathedral|Market|Beach|Square|Bridge|Garden|Gallery|Stadium|Airport|Station|Basilica|Arc|Castle|Restaurant|Café|Hotel))\b',
        # Famous landmarks
        r'\b(Eiffel Tower|Louvre Museum|Notre-Dame Cathedral|Arc de Triomphe|Sacré-Cœur Basilica|Times Square|Central Park|Big Ben|London Eye|Statue of Liberty|Golden Gate Bridge|Colosseum|Vatican City|Trevi Fountain|Roman Forum|Pantheon)\b',
        # Hotels and restaurants with common names
        r'\b([A-Z][a-zA-Z\s&\']+(?:Restaurant|Café|Hotel|Inn|Lodge|Bistro|Brasserie|Tavern))\b'
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
                    if clean_match and len(clean_match) > 3:
                        locations.add(clean_match)
    
    return list(locations)

# Initialize optimized services
gmaps_service = optimized_gmaps_service = CostOptimizedGoogleMapsService()
ai_service = optimized_ai_service = CostOptimizedAIService()
