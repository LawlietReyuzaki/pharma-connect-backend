let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let audioContext;
let audioStream;

// Function to start voice recording
async function startVoiceRecording() {
    try {
        // Stop any existing recording first
        if (isRecording) {
            stopVoiceRecording();
            return;
        }

        // Initialize audio context if not already done
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Get microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                sampleRate: 44100,
                sampleSize: 16
            } 
        });

        // Try different mime types until we find one that works
        const mimeTypes = [
            'audio/webm;codecs=opus',
            'audio/ogg;codecs=opus',
            'audio/webm',
            'audio/ogg',
            'audio/wav',
            'audio/mp4',
            '' // Let the browser decide
        ];

        let options = {};
        for (const mimeType of mimeTypes) {
            if (mimeType && MediaRecorder.isTypeSupported(mimeType)) {
                options = { mimeType };
                console.log('Using mimeType:', mimeType);
                break;
            }
        }

        mediaRecorder = new MediaRecorder(audioStream, options);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            // Use the same mime type that was used for recording, or default to webm
            const mimeType = mediaRecorder.mimeType || 'audio/webm';
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            await sendAudioToBackend(audioBlob);
            audioChunks = [];
            if (audioStream) {
                audioStream.getTracks().forEach(track => track.stop());
                audioStream = null;
            }
        };

        // Start recording
        mediaRecorder.start(100); // Collect 100ms chunks
        isRecording = true;
        updateUIForRecording(true);
        updateChatStatus('Listening...');

    } catch (error) {
        console.error('Error accessing microphone:', error);
        showError('Could not access microphone. Please check permissions.');
    }
}

// Function to stop voice recording
function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        updateUIForRecording(false);
        updateChatStatus('Processing...');
    }
}

// Toggle recording state
function toggleVoiceInput() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

// Send audio to backend for transcription
async function sendAudioToBackend(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    // Determine the endpoint based on current language
    const currentLanguage = window.currentLanguage;
    console.log('Current language:', currentLanguage);
    const endpoint = currentLanguage === 'ur' 
        ? '/api/chat/transcribe-urdu'
        : '/api/chat/transcribe-english';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success && data.transcript) {
            // Set the transcribed text in the input field
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.value = data.transcript;
                // Auto-submit the form
                const chatForm = document.querySelector('form#chatForm');
                if (chatForm) {
                    chatForm.dispatchEvent(new Event('submit'));
                }
            }
        } else {
            throw new Error(data.error || 'Failed to transcribe audio');
        }
    } catch (error) {
        console.error('Error sending audio to backend:', error);
        showError('Failed to transcribe audio. Please try again.');
    } finally {
        updateChatStatus('Ready');
    }
}

// Update UI based on recording state
function updateUIForRecording(isRecording) {
    const voiceButton = document.getElementById('voiceButton');
    const voiceIcon = voiceButton?.querySelector('i');

    if (!voiceButton || !voiceIcon) return;

    if (isRecording) {
        voiceButton.classList.add('btn-danger');
        voiceButton.classList.remove('btn-outline-danger');
        voiceIcon.className = 'fas fa-stop';
    } else {
        voiceButton.classList.remove('btn-danger');
        voiceButton.classList.add('btn-outline-danger');
        voiceIcon.className = 'fas fa-microphone';
    }
}

// Helper function to show error messages
function showError(message) {
    console.error(message);
    updateChatStatus('Error: ' + message);
}

// Helper function to update chat status
function updateChatStatus(message) {
    const statusElement = document.getElementById('recordingStatus');
    if (statusElement) {
        statusElement.textContent = message;
    }
}