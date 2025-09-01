from flask import Blueprint, request, jsonify, send_file
from services.chatbot import generate_response, log_chat_interaction
import speech_recognition as sr
import uuid
import logging
import os
import time
from gtts import gTTS
import io
from werkzeug.utils import secure_filename

bp = Blueprint("chatbot", __name__)

# TTS Configuration
TTS_API_KEY = "8f1e5568-0d81-477a-a023-259fff2346d0"
TTS_BASE_URL = "https://aivoov.com/api/v8"
URDU_VOICE_ID = "86cad650-a467-486c-bc86-15d1615084e0"

@bp.route("/", methods=["POST"])
def chat():
    """Main chatbot endpoint"""
    try:
        print("Chat endpoint called")
        # print(request.get_json())
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Get or create session ID
        session_id = data.get("session_id", str(uuid.uuid4()))
        prefer_urdu = data.get("language") == "ur"
        user_id = data.get("user_id")  # Optional, from authenticated users
        
        # Generate response
        response_data = generate_response(
            text=message,
            prefer_urdu=prefer_urdu,
            session_id=session_id
        )
        # print(response_data)
        
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

@bp.route("/transcribe-urdu", methods=["POST"])
def transcribe_urdu_audio():
    """
    Endpoint to transcribe Urdu speech from an audio file
    Accepts: multipart/form-data with 'audio' file
    Returns: JSON with transcribed text or error message
    """
    try:
        # Check if the post request has the file part
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if audio_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if audio_file:
            # Create uploads directory if it doesn't exist
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save the uploaded file temporarily
            filename = secure_filename(audio_file.filename)
            temp_path = os.path.join(upload_folder, filename)
            audio_file.save(temp_path)
            
            try:
                # Transcribe the audio file
                recognizer = sr.Recognizer()
                
                # Convert the file to WAV if it's not already
                try:
                    import pydub
                    import tempfile
                    
                    # Create a temporary WAV file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                        # Convert to WAV using pydub
                        sound = pydub.AudioSegment.from_file(temp_path)
                        sound = sound.set_frame_rate(16000).set_channels(1)
                        sound.export(temp_wav.name, format='wav')
                        
                        # Use the WAV file for recognition
                        with sr.AudioFile(temp_wav.name) as source:
                            audio = recognizer.record(source)
                            text = recognizer.recognize_google(audio, language="ur")
                        
                        # Clean up the temporary WAV file
                        try:
                            os.unlink(temp_wav.name)
                        except:
                            pass
                            
                except ImportError:
                    # Fall back to direct WAV processing if pydub is not available
                    with sr.AudioFile(temp_path) as source:
                        audio = recognizer.record(source)
                        text = recognizer.recognize_google(audio, language="ur")
                
                # Clean up the temporary file
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logging.warning(f"Could not remove temporary file {temp_path}: {e}")
                
                return jsonify({
                    "success": True,
                    "transcript": text
                })
                
            except sr.UnknownValueError:
                return jsonify({
                    "success": False,
                    "error": "Could not understand the audio"
                }), 400
                
            except sr.RequestError as e:
                return jsonify({
                    "success": False,
                    "error": f"Speech recognition service error: {str(e)}"
                }), 500
                
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred during audio processing"
        }), 500


@bp.route("/transcribe-english", methods=["POST"])
def transcribe_english_audio():
    """
    Endpoint to transcribe English speech from an audio file
    Accepts: multipart/form-data with 'audio' file
    Returns: JSON with transcribed text or error message
    """
    try:
        # Check if the post request has the file part
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if audio_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if audio_file:
            # Create uploads directory if it doesn't exist
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save the uploaded file temporarily
            filename = secure_filename(audio_file.filename)
            temp_path = os.path.join(upload_folder, filename)
            audio_file.save(temp_path)
            
            try:
                # Transcribe the audio file
                recognizer = sr.Recognizer()
                
                # Convert the file to WAV if it's not already
                try:
                    import pydub
                    import tempfile
                    
                    # Create a temporary WAV file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                        # Convert to WAV using pydub
                        sound = pydub.AudioSegment.from_file(temp_path)
                        sound = sound.set_frame_rate(16000).set_channels(1)
                        sound.export(temp_wav.name, format='wav')
                        
                        # Use the WAV file for recognition
                        with sr.AudioFile(temp_wav.name) as source:
                            audio = recognizer.record(source)
                            text = recognizer.recognize_google(audio, language="en-US")
                        
                        # Clean up the temporary WAV file
                        try:
                            os.unlink(temp_wav.name)
                        except:
                            pass
                            
                except ImportError:
                    # Fall back to direct WAV processing if pydub is not available
                    with sr.AudioFile(temp_path) as source:
                        audio = recognizer.record(source)
                        text = recognizer.recognize_google(audio, language="en-US")
                
                # Clean up the temporary file
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logging.warning(f"Could not remove temporary file {temp_path}: {e}")
                
                return jsonify({
                    "success": True,
                    "transcript": text
                })
                
            except sr.UnknownValueError:
                return jsonify({
                    "success": False,
                    "error": "Could not understand the audio"
                }), 400
                
            except sr.RequestError as e:
                return jsonify({
                    "success": False,
                    "error": f"Speech recognition service error: {str(e)}"
                }), 500
                
    except Exception as e:
        logging.error(f"English transcription error: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred during audio processing"
        }), 500


@bp.route("/speak-urdu", methods=["POST"])
def speak_urdu():
    """
    Endpoint to convert Urdu text to speech
    Accepts: JSON with 'text' field containing Urdu text
    Returns: JSON with audio file URL or error message
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Generate speech using gTTS
        tts = gTTS(text=text, lang='ur')
        
        # Create a file-like buffer to store the audio
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)  # Rewind the buffer to the beginning
        
        # Return the audio file directly from memory
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"speech_{int(time.time())}.mp3"
        )
        
    except Exception as e:
        logging.error(f"TTS error: {e}")
        return jsonify({
            "error": "Failed to process text-to-speech request",
            "success": False
        }), 500
