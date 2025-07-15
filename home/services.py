import os
import base64
from django.conf import settings
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class AIService:
    """Service class for handling OpenAI GPT-4 interactions"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
    
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

    def generate_response(self, message, file_attachment=None, voice_attachment=None, chat_history=None):
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
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
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

# Create a singleton instance
ai_service = AIService()
