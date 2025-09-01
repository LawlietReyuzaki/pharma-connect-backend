import os
import re
import logging
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI client
client = None
if os.getenv("OPENAI_API_KEY"):
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")

# Medical red flags in both English and Urdu
RED_FLAGS = [
    # English patterns
    r"chest pain", r"heart attack", r"stroke", r"seizure", r"unconscious", 
    r"severe bleeding", r"difficulty breathing", r"can't breathe",
    r"suicidal", r"suicide", r"overdose", r"poisoning",
    
    # Urdu patterns
    r"سینے میں درد", r"سانس.*میں دقت", r"سانس.*نہیں آ رہا", r"بیہوش", 
    r"خون.*بہت زیادہ", r"دل کا دورہ", r"فالج", r"خودکشی"
]

# Medical disclaimer in Urdu and English
DISCLAIMER_UR = (
    "⚠️ اہم: یہ معلومات طبی مشورہ نہیں ہے۔ ہنگامی صورتحال میں فوراً 1122 پر کال کریں یا "
    "قریبی ہسپتال جائیں۔ Red Dot Pharmacy آپ کی صحت کی دیکھ بھال کرتا ہے۔"
)

DISCLAIMER_EN = (
    "⚠️ Important: This information is not medical advice. In emergency situations, "
    "immediately call 1122 or visit the nearest hospital. Red Dot Pharmacy cares for your health."
)

def needs_escalation(text: str) -> bool:
    """Check if message contains medical red flags requiring immediate attention"""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in RED_FLAGS)

def generate_response(text: str, prefer_urdu=True, session_id=None) -> dict:
    """
    Generate chatbot response with medical guardrails
    Returns: {
        'message': str,
        'flagged': bool,
        'needs_doctor': bool,
        'suggested_medicines': list
    }
    """
    
    # Check for medical emergencies
    if needs_escalation(text):
        warning_msg = DISCLAIMER_UR if prefer_urdu else DISCLAIMER_EN
        
        if prefer_urdu:
            emergency_msg = (
                f"{warning_msg}\n\n"
                "🚨 آپ کی علامات سنگین ہو سکتی ہیں۔ براہ کرم فوراً:\n"
                "• 1122 پر کال کریں\n"
                "• قریبی ہسپتال جائیں\n"
                "• یا Red Dot Pharmacy میں آئیں تاکہ ہمارے ڈاکٹر سے مشورہ کر سکیں"
            )
        else:
            emergency_msg = (
                f"{warning_msg}\n\n"
                "🚨 Your symptoms may be serious. Please immediately:\n"
                "• Call 1122\n"
                "• Visit the nearest hospital\n"
                "• Or come to Red Dot Pharmacy to consult with our doctors"
            )
        
        return {
            'message': emergency_msg,
            'flagged': True,
            'needs_doctor': True,
            'suggested_medicines': []
        }
    
    # Try to generate AI response if OpenAI is available
    if client:
        try:
            # System prompt with Red Dot Pharmacy context
            system_prompt = (
                "You are a helpful medical assistant for Red Dot Pharmacy in Pakistan. "
                "You provide general health guidance and medicine information. "
                "Always remind users that this is not professional medical advice. "
                "Suggest they visit Red Dot Pharmacy for proper consultation. "
                "Keep responses concise and helpful. "
                "If asked about medicines, suggest common over-the-counter options available in Pakistan. "
            )
            
            if prefer_urdu:
                system_prompt += (
                    "Respond in Urdu. Use respectful language. "
                    "Always end with reminder to visit Red Dot Pharmacy for proper consultation."
                )
            
            response = client.chat.completions.create(
                model="gpt-5",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            ai_message = response.choices[0].message.content
            if ai_message:
                ai_message = ai_message.strip()
            else:
                ai_message = "I apologize, but I couldn't process your request. Please try again."
            
            # Add Red Dot Pharmacy disclaimer
            disclaimer = DISCLAIMER_UR if prefer_urdu else DISCLAIMER_EN
            final_message = f"{ai_message}\n\n{disclaimer}"
            
            return {
                'message': final_message,
                'flagged': False,
                'needs_doctor': False,
                'suggested_medicines': []
            }
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            # Fall through to offline response
    
    # Offline fallback response
    if prefer_urdu:
        offline_msg = (
            "شکریہ آپ کے سوال کا! Red Dot Pharmacy میں ہمارے پاس تجربہ کار ڈاکٹرز موجود ہیں۔\n\n"
            "بہتر رہنمائی کے لیے:\n"
            "• اپنی علامات تفصیل سے بتائیں\n"
            "• دوا کی تاریخ شیئر کریں\n"
            "• آن لائن ملاقات بک کریں\n"
            "• یا ہمارے فارمیسی آئیں\n\n"
            f"{DISCLAIMER_UR}"
        )
    else:
        offline_msg = (
            "Thank you for your question! Red Dot Pharmacy has experienced doctors available.\n\n"
            "For better guidance:\n"
            "• Describe your symptoms in detail\n"
            "• Share your medication history\n"
            "• Book an online consultation\n"
            "• Or visit our pharmacy\n\n"
            f"{DISCLAIMER_EN}"
        )
    
    return {
        'message': offline_msg,
        'flagged': False,
        'needs_doctor': True,
        'suggested_medicines': []
    }

def log_chat_interaction(session_id, user_message, bot_response, user_id=None, flagged=False):
    """Log chat interaction for analysis and improvement"""
    try:
        from app import db
        from models import ChatLog
        
        chat_log = ChatLog()
        chat_log.user_id = user_id
        chat_log.session_id = session_id
        chat_log.message = user_message
        chat_log.response = bot_response
        chat_log.language = "ur"  # Default to Urdu
        chat_log.flagged = flagged
        
        db.session.add(chat_log)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Failed to log chat interaction: {e}")
