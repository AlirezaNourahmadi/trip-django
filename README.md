# Trip-Django 🌍

A Django-based travel planning application with an AI-powered chatbot that supports text, file attachments, images, and voice messages.

## Features

- **AI Chatbot**: Interactive travel assistant with support for:
  - Text messages
  - File attachments (PDF, DOC, images, etc.)
  - Voice messages and recording
  - Speech-to-text recognition
  - Real-time chat interface

- **User Management**: 
  - User registration and authentication
  - User profiles
  - Trip request history

- **Trip Planning**:
  - Create trip requests with destinations, budgets, and durations
  - Generate travel plans (placeholder for LLM integration)
  - Download plans as PDF files

- **Admin Interface**:
  - Manage users, destinations, and chat messages
  - Monitor trip requests and generated plans

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL (or change to SQLite for development)
- pip (Python package manager)

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

## GPT-4 Integration ✅

The chatbot is now fully integrated with **OpenAI GPT-4 Turbo** for intelligent travel assistance!

### Features:
- **GPT-4 Turbo**: Latest OpenAI model for superior responses
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
