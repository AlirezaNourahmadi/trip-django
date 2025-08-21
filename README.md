# 🌍 TripAI - Intelligent Travel Planning Platform

> *Your AI-powered travel companion for creating personalized, professional trip itineraries with real-time location data and beautiful PDF reports.*

[![Django](https://img.shields.io/badge/Django-5.1.6-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenAI GPT-5](https://img.shields.io/badge/OpenAI-GPT--5-orange.svg)](https://openai.com)
[![Google Maps](https://img.shields.io/badge/Google-Maps%20API-red.svg)](https://developers.google.com/maps)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Key Features

### 🤖 **Advanced AI Travel Assistant**
- **GPT-5 Integration**: Latest OpenAI model for intelligent travel recommendations
- **Multi-Modal Communication**: Text, voice, file uploads, and image analysis
- **Contextual Conversations**: Maintains chat history for personalized responses
- **Real-Time Processing**: Instant responses with typing indicators
- **Speech Recognition**: Browser-based voice-to-text input
- **File Analysis**: Upload documents, images, and audio for travel planning

### 🗺️ **Google Maps Integration**
- **Places API**: Real location data with photos, ratings, and details
- **Smart Location Extraction**: AI-powered location detection from itineraries
- **Interactive Maps**: Clickable links for every destination
- **Photo Collections**: Up to 3 high-quality photos per location
- **Autocomplete Search**: Intelligent destination suggestions
- **Geo-Coordinates**: Precise location mapping and directions

### 📄 **Professional PDF Generation**
- **ReportLab Engine**: High-quality PDF creation with custom styling
- **Embedded Media**: Location photos and maps integrated in documents
- **Interactive Elements**: Clickable Google Maps links
- **Emoji Support**: Modern, visually appealing formatting
- **Multi-Format Export**: PDF, text, and web-based viewing
- **Manual Regeneration**: On-demand PDF creation and updates

### 👥 **User Management & Profiles**
- **Secure Authentication**: Registration, login, and user sessions
- **Personalized Dashboards**: Individual trip history and preferences
- **Trip Collections**: Organized view of all travel plans
- **Support Tickets**: Integrated help system with chat context
- **Progress Tracking**: Real-time status updates for trip generation

### 🧳 **Intelligent Trip Planning**
- **AI-Powered Itineraries**: Customized plans based on budget, duration, and interests
- **Background Processing**: Non-blocking trip generation
- **Status Monitoring**: Real-time progress tracking with visual feedback
- **Fallback Systems**: Enhanced plans even when AI APIs are unavailable
- **Multiple Destinations**: Support for complex, multi-city travel plans
- **Budget Optimization**: Cost-effective recommendations within user constraints

### 🎨 **Modern User Interface**
- **Responsive Design**: Perfect on desktop, tablet, and mobile devices
- **Glass Morphism**: Modern UI with blur effects and gradients
- **Smooth Animations**: CSS transitions and micro-interactions
- **Loading States**: Visual feedback during processing
- **Interactive Cards**: Hover effects and dynamic content
- **Dark/Light Themes**: Consistent styling across all pages

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL (or change to SQLite for development)
- pip (Python package manager)
- **reportlab** (for PDF generation)

### Installation

1. **Clone the repository**:
   ```bash
   cd ~/Desktop/trip-django
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**:
   
   For PostgreSQL (current setup):
   - Create a PostgreSQL database named 'Hatef'
   - Update `main/settings.py` with your database credentials
   
   For SQLite (easier for development):
   - Change the DATABASES setting in `main/settings.py` to:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
       }
   }
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate sample destinations**:
   ```bash
   python manage.py populate_destinations
   ```

8. **Collect static files** (if needed):
   ```bash
   python manage.py collectstatic
   ```

9. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

10. **Access the application**:
    - Main site: http://127.0.0.1:8000/
    - Admin panel: http://127.0.0.1:8000/admin/
    - Chatbot: http://127.0.0.1:8000/chatbot/

## Usage

### Chatbot Features

1. **Text Chat**: Type messages and get AI responses about travel planning
2. **File Attachments**: Click the paperclip icon to attach travel documents, itineraries, etc.
3. **Image Attachments**: Click the image icon to attach photos
4. **Voice Recording**: Click the microphone icon to record voice messages
5. **Speech Recognition**: Click the microphone in the header to use speech-to-text
6. **Clear Chat**: Click the trash icon to clear chat history

### Browser Permissions

For voice features to work, you'll need to grant microphone permissions when prompted by your browser.

### Supported File Types

- **Images**: .jpg, .jpeg, .png, .gif
- **Documents**: .pdf, .doc, .docx, .txt, .csv, .xlsx
- **Audio**: .mp3, .wav, .ogg, .m4a

## GPT-5 Integration ✅

The chatbot is now fully integrated with **OpenAI GPT-5** for intelligent travel assistance!

### Features:
- **GPT-5**: Latest OpenAI model for superior responses
- **Vision Support**: Can analyze uploaded images and identify locations
- **Context Awareness**: Maintains conversation history for better responses
- **Specialized Prompts**: Optimized for travel planning and recommendations
- **Fallback System**: Graceful handling of API errors

### Configuration:
The AI service is configured in `home/services.py` with:
- Professional travel assistant prompts
- Image analysis capabilities
- Chat history context
- Error handling and fallbacks

Environment variables (see .env.example):
- OPENAI_MODEL (default: gpt-5)
- TEMPERATURE (default: 1 for gpt-5; only used for gpt-4 family)
- MAX_TOKENS (mapped to max_completion_tokens for gpt-5)

### API Usage:
The system uses environment variables for secure API key management. All OpenAI interactions are handled through the `AIService` class.

## Production Deployment

Before deploying to production:

1. Set `DEBUG = False` in settings.py
2. Use environment variables for sensitive data (database credentials, secret keys)
3. Configure proper static file serving
4. Set up HTTPS
5. Configure allowed hosts
6. Use a production database
7. Set up proper logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational/prototype purposes. Please add your own license as needed.

## Support

For issues or questions, please create an issue in the repository or contact the development team.
