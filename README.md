# Red Dot Pharmacy

A comprehensive online pharmacy platform built with Flask featuring:

## Features
- **Medicine Shopping**: Browse and purchase medications online
- **Doctor Consultations**: Book video appointments with healthcare professionals  
- **AI-Powered Chatbot**: Medical assistance in English and Urdu with safety guardrails
- **Admin Dashboard**: Manage appointments, medicines, users, and time slots
- **Google Authentication**: Secure login integration for appointments

## Tech Stack
- **Backend**: Flask, SQLAlchemy, JWT Authentication
- **Frontend**: Bootstrap 5, JavaScript, Chart.js  
- **Database**: PostgreSQL (Replit Database)
- **AI**: OpenAI integration for chatbot responses
- **Video Calls**: Jitsi Meet integration

## Admin Access
- **Email**: admin.reddotpharmacy@gmail.com
- **Password**: admin

## Installation & Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables in `.env`
4. Run the application: `gunicorn --bind 0.0.0.0:5000 main:app`

## Environment Variables Required
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `OPENAI_API_KEY`: OpenAI API key for chatbot (optional)
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth client ID (optional)
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth client secret (optional)

## Project Structure
- `main.py`: Application entry point
- `models.py`: Database models
- `routes/`: API route handlers
- `services/`: Business logic and external service integrations
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and assets

## License
MIT License