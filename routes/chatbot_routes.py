from flask import Blueprint, request, jsonify
from services.chatbot import generate_response, log_chat_interaction
import uuid
import logging

bp = Blueprint("chatbot", __name__)

@bp.route("/", methods=["POST"])
def chat():
    """Main chatbot endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get("text", "").strip()
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Get or create session ID
        session_id = data.get("session_id", str(uuid.uuid4()))
        prefer_urdu = data.get("prefer_urdu", True)
        user_id = data.get("user_id")  # Optional, from authenticated users
        
        # Generate response
        response_data = generate_response(
            text=message,
            prefer_urdu=prefer_urdu,
            session_id=session_id
        )
        
        # Log the interaction
        log_chat_interaction(
            session_id=session_id,
            user_message=message,
            bot_response=response_data['message'],
            user_id=user_id,
            flagged=response_data['flagged']
        )
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": response_data['message'],
            "flagged": response_data['flagged'],
            "needs_doctor": response_data['needs_doctor'],
            "suggested_medicines": response_data['suggested_medicines']
        })
        
    except Exception as e:
        logging.error(f"Chatbot error: {e}")
        return jsonify({
            "error": "Sorry, I'm having trouble right now. Please try again later.",
            "success": False
        }), 500

@bp.route("/voice", methods=["POST"])
def voice_chat():
    """Voice-enabled chat endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Handle voice input (transcript from client-side Speech Recognition)
        transcript = data.get("transcript", "").strip()
        if not transcript:
            return jsonify({"error": "No transcript provided"}), 400
        
        session_id = data.get("session_id", str(uuid.uuid4()))
        prefer_urdu = data.get("prefer_urdu", True)
        user_id = data.get("user_id")
        
        # Generate response using the same chatbot logic
        response_data = generate_response(
            text=transcript,
            prefer_urdu=prefer_urdu,
            session_id=session_id
        )
        
        # Log the voice interaction
        log_chat_interaction(
            session_id=session_id,
            user_message=f"[VOICE] {transcript}",
            bot_response=response_data['message'],
            user_id=user_id,
            flagged=response_data['flagged']
        )
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "transcript": transcript,
            "message": response_data['message'],
            "flagged": response_data['flagged'],
            "needs_doctor": response_data['needs_doctor'],
            "suggested_medicines": response_data['suggested_medicines'],
            "voice_enabled": True
        })
        
    except Exception as e:
        logging.error(f"Voice chat error: {e}")
        return jsonify({
            "error": "Voice chat is temporarily unavailable. Please try text chat.",
            "success": False
        }), 500

@bp.route("/history/<session_id>", methods=["GET"])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        from models import ChatLog
        
        # Get chat logs for this session
        logs = ChatLog.query.filter_by(session_id=session_id).order_by(ChatLog.created_at).all()
        
        history = []
        for log in logs:
            history.append({
                "message": log.message,
                "response": log.response,
                "timestamp": log.created_at.isoformat(),
                "flagged": log.flagged
            })
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history
        })
        
    except Exception as e:
        logging.error(f"Chat history error: {e}")
        return jsonify({
            "error": "Failed to retrieve chat history",
            "success": False
        }), 500

@bp.route("/sessions", methods=["GET"])
def get_user_sessions():
    """Get chat sessions for authenticated user"""
    try:
        from services.auth import get_current_user
        from models import ChatLog
        
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get unique sessions for this user
        sessions = ChatLog.query.filter_by(user_id=user.id)\
                               .with_entities(ChatLog.session_id, ChatLog.created_at)\
                               .distinct(ChatLog.session_id)\
                               .order_by(ChatLog.created_at.desc())\
                               .limit(10).all()
        
        session_list = []
        for session in sessions:
            # Get first message of each session for preview
            first_log = ChatLog.query.filter_by(
                user_id=user.id, 
                session_id=session.session_id
            ).first()
            
            session_list.append({
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "preview": (first_log.message[:50] + "...") if (first_log and first_log.message and len(first_log.message) > 50) else (first_log.message if first_log and first_log.message else "No preview available")
            })
        
        return jsonify({
            "success": True,
            "sessions": session_list
        })
        
    except Exception as e:
        logging.error(f"User sessions error: {e}")
        return jsonify({
            "error": "Failed to retrieve chat sessions",
            "success": False
        }), 500
