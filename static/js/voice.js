// Red Dot Pharmacy - Voice Assistant Integration
// Handles speech recognition and synthesis for Urdu and English

class VoiceAssistant {
    constructor() {
        this.isSupported = this.checkSupport();
        this.isListening = false;
        this.currentLanguage = 'ur-PK'; // Default to Urdu
        this.voices = [];
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        
        this.initializeVoices();
        this.setupEventListeners();
    }

    // ============ INITIALIZATION ============
    
    checkSupport() {
        const hasSpeechRecognition = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        const hasSpeechSynthesis = 'speechSynthesis' in window;
        
        if (!hasSpeechRecognition) {
            console.warn('Speech Recognition not supported in this browser');
        }
        
        if (!hasSpeechSynthesis) {
            console.warn('Speech Synthesis not supported in this browser');
        }
        
        return {
            recognition: hasSpeechRecognition,
            synthesis: hasSpeechSynthesis
        };
    }

    initializeVoices() {
        if (!this.isSupported.synthesis) return;

        // Load voices (may need to wait for them to be loaded)
        const loadVoices = () => {
            this.voices = this.synthesis.getVoices();
            this.categorizeVoices();
        };

        // Voices may not be loaded immediately
        if (this.synthesis.getVoices().length === 0) {
            this.synthesis.addEventListener('voiceschanged', loadVoices);
        } else {
            loadVoices();
        }
    }

    categorizeVoices() {
        this.voiceMap = {
            'ur-PK': this.voices.filter(voice => 
                voice.lang.includes('ur') || 
                voice.name.toLowerCase().includes('urdu')
            ),
            'en-US': this.voices.filter(voice => 
                voice.lang.includes('en-US') || 
                voice.lang.includes('en-GB')
            ),
            'en-GB': this.voices.filter(voice => 
                voice.lang.includes('en-GB')
            )
        };

        console.log('Available voices:', this.voiceMap);
    }

    setupEventListeners() {
        // Listen for language changes from chatbot
        document.addEventListener('languageChanged', (event) => {
            this.currentLanguage = event.detail.language;
        });

        // Listen for page visibility changes to stop recognition
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isListening) {
                this.stopListening();
            }
        });
    }

    // ============ SPEECH RECOGNITION ============
    
    startListening(options = {}) {
        if (!this.isSupported.recognition) {
            throw new Error('Speech recognition not supported');
        }

        if (this.isListening) {
            this.stopListening();
            return;
        }

        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            // Configure recognition
            this.recognition.lang = options.language || this.currentLanguage;
            this.recognition.continuous = options.continuous || false;
            this.recognition.interimResults = options.interimResults || false;
            this.recognition.maxAlternatives = options.maxAlternatives || 1;

            // Set up event handlers
            this.recognition.onstart = () => {
                this.isListening = true;
                this.onListeningStart(options.onStart);
            };

            this.recognition.onresult = (event) => {
                this.handleRecognitionResult(event, options.onResult);
            };

            this.recognition.onerror = (event) => {
                this.handleRecognitionError(event, options.onError);
            };

            this.recognition.onend = () => {
                this.isListening = false;
                this.onListeningEnd(options.onEnd);
            };

            // Start recognition
            this.recognition.start();
            
        } catch (error) {
            console.error('Failed to start speech recognition:', error);
            throw error;
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    handleRecognitionResult(event, callback) {
        const results = Array.from(event.results);
        const finalResults = results.filter(result => result.isFinal);
        
        if (finalResults.length > 0) {
            const transcript = finalResults[0][0].transcript.trim();
            const confidence = finalResults[0][0].confidence;
            
            const result = {
                transcript,
                confidence,
                language: this.currentLanguage,
                isFinal: true
            };
            
            if (callback) {
                callback(result);
            }
            
            // Dispatch custom event
            this.dispatchRecognitionEvent('speechResult', result);
        }
        
        // Handle interim results
        const interimResults = results.filter(result => !result.isFinal);
        if (interimResults.length > 0) {
            const interimTranscript = interimResults[0][0].transcript;
            const interimResult = {
                transcript: interimTranscript,
                confidence: interimResults[0][0].confidence,
                language: this.currentLanguage,
                isFinal: false
            };
            
            this.dispatchRecognitionEvent('speechInterim', interimResult);
        }
    }

    handleRecognitionError(event, callback) {
        const error = {
            type: event.error,
            message: this.getErrorMessage(event.error),
            language: this.currentLanguage
        };
        
        console.error('Speech recognition error:', error);
        
        if (callback) {
            callback(error);
        }
        
        this.dispatchRecognitionEvent('speechError', error);
    }

    getErrorMessage(errorType) {
        const errorMessages = {
            'no-speech': 'No speech detected. Please try again.',
            'audio-capture': 'Microphone not available or not accessible.',
            'not-allowed': 'Microphone access denied. Please allow microphone access.',
            'network': 'Network error occurred during speech recognition.',
            'aborted': 'Speech recognition was aborted.',
            'bad-grammar': 'Grammar error in speech recognition.',
            'language-not-supported': 'Language not supported for speech recognition.'
        };
        
        return errorMessages[errorType] || `Speech recognition error: ${errorType}`;
    }

    onListeningStart(callback) {
        if (callback) callback();
        this.dispatchRecognitionEvent('speechStart', { language: this.currentLanguage });
    }

    onListeningEnd(callback) {
        if (callback) callback();
        this.dispatchRecognitionEvent('speechEnd', { language: this.currentLanguage });
    }

    dispatchRecognitionEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    // ============ SPEECH SYNTHESIS ============
    
    speak(text, options = {}) {
        if (!this.isSupported.synthesis) {
            throw new Error('Speech synthesis not supported');
        }

        return new Promise((resolve, reject) => {
            try {
                // Cancel any ongoing speech
                this.synthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(text);
                
                // Configure utterance
                utterance.lang = options.language || this.currentLanguage;
                utterance.rate = options.rate || 0.8;
                utterance.pitch = options.pitch || 1;
                utterance.volume = options.volume || 0.8;
                
                // Set voice
                const voice = this.getBestVoice(utterance.lang, options.voiceGender);
                if (voice) {
                    utterance.voice = voice;
                }
                
                // Set up event handlers
                utterance.onstart = () => {
                    if (options.onStart) options.onStart();
                    this.dispatchSynthesisEvent('speechStart', { text, language: utterance.lang });
                };
                
                utterance.onend = () => {
                    if (options.onEnd) options.onEnd();
                    this.dispatchSynthesisEvent('speechEnd', { text, language: utterance.lang });
                    resolve();
                };
                
                utterance.onerror = (event) => {
                    const error = new Error(`Speech synthesis error: ${event.error}`);
                    if (options.onError) options.onError(error);
                    this.dispatchSynthesisEvent('speechError', { error: event.error, text });
                    reject(error);
                };
                
                utterance.onpause = () => {
                    this.dispatchSynthesisEvent('speechPause', { text });
                };
                
                utterance.onresume = () => {
                    this.dispatchSynthesisEvent('speechResume', { text });
                };
                
                // Start speaking
                this.synthesis.speak(utterance);
                
            } catch (error) {
                reject(error);
            }
        });
    }

    getBestVoice(language, preferredGender = null) {
        const availableVoices = this.voiceMap[language] || [];
        
        if (availableVoices.length === 0) {
            // Fallback to any voice with the language
            return this.voices.find(voice => voice.lang.includes(language.split('-')[0]));
        }
        
        // Prefer specific gender if specified
        if (preferredGender) {
            const genderVoices = availableVoices.filter(voice => 
                voice.name.toLowerCase().includes(preferredGender.toLowerCase())
            );
            if (genderVoices.length > 0) {
                return genderVoices[0];
            }
        }
        
        // Return first available voice for the language
        return availableVoices[0];
    }

    stopSpeaking() {
        if (this.synthesis.speaking) {
            this.synthesis.cancel();
        }
    }

    pauseSpeaking() {
        if (this.synthesis.speaking) {
            this.synthesis.pause();
        }
    }

    resumeSpeaking() {
        if (this.synthesis.paused) {
            this.synthesis.resume();
        }
    }

    dispatchSynthesisEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    // ============ LANGUAGE MANAGEMENT ============
    
    setLanguage(language) {
        const supportedLanguages = ['ur-PK', 'en-US', 'en-GB'];
        
        if (supportedLanguages.includes(language)) {
            this.currentLanguage = language;
            
            // Dispatch language change event
            const event = new CustomEvent('languageChanged', { 
                detail: { language } 
            });
            document.dispatchEvent(event);
            
            return true;
        }
        
        console.warn(`Language ${language} not supported`);
        return false;
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }

    getSupportedLanguages() {
        return Object.keys(this.voiceMap);
    }

    // ============ VOICE COMMANDS ============
    
    setupVoiceCommands(commands) {
        this.voiceCommands = commands;
        
        document.addEventListener('speechResult', (event) => {
            this.processVoiceCommand(event.detail.transcript);
        });
    }

    processVoiceCommand(transcript) {
        if (!this.voiceCommands) return;
        
        const lowerTranscript = transcript.toLowerCase();
        
        for (const [command, action] of Object.entries(this.voiceCommands)) {
            if (lowerTranscript.includes(command.toLowerCase())) {
                try {
                    if (typeof action === 'function') {
                        action(transcript);
                    } else if (typeof action === 'string') {
                        // Execute as a function name
                        if (window[action] && typeof window[action] === 'function') {
                            window[action](transcript);
                        }
                    }
                } catch (error) {
                    console.error(`Error executing voice command "${command}":`, error);
                }
                break;
            }
        }
    }

    // ============ MEDICAL VOICE FEATURES ============
    
    speakMedicalAlert(message) {
        return this.speak(message, {
            rate: 0.7, // Slower for important information
            pitch: 1.1, // Slightly higher pitch for urgency
            volume: 1.0, // Full volume
            language: this.currentLanguage
        });
    }

    speakMedicineInformation(medicine) {
        const urduText = `${medicine.name} کی قیمت ${medicine.price} روپے ہے۔ یہ ${medicine.category || 'عام'} کیٹگری میں آتا ہے۔`;
        const englishText = `${medicine.name} costs ${medicine.price} rupees. It belongs to ${medicine.category || 'general'} category.`;
        
        const text = this.currentLanguage.includes('ur') ? urduText : englishText;
        
        return this.speak(text, {
            rate: 0.8,
            language: this.currentLanguage
        });
    }

    speakAppointmentInfo(appointment) {
        const date = new Date(appointment.start_time);
        const urduText = `آپ کی ملاقات ${appointment.doctor_name} کے ساتھ ${date.toLocaleDateString('ur-PK')} کو ${date.toLocaleTimeString('ur-PK')} بجے ہے۔`;
        const englishText = `Your appointment with ${appointment.doctor_name} is on ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}.`;
        
        const text = this.currentLanguage.includes('ur') ? urduText : englishText;
        
        return this.speak(text, {
            language: this.currentLanguage
        });
    }

    // ============ ACCESSIBILITY FEATURES ============
    
    announcePageContent(content) {
        return this.speak(content, {
            rate: 0.9,
            volume: 0.7,
            language: this.currentLanguage
        });
    }

    announceNavigation(element) {
        const urduText = `نیویگیٹ کر رہے ہیں ${element}`;
        const englishText = `Navigating to ${element}`;
        
        const text = this.currentLanguage.includes('ur') ? urduText : englishText;
        
        return this.speak(text, {
            rate: 1.0,
            volume: 0.6
        });
    }

    announceError(error) {
        const urduText = `خرابی: ${error}`;
        const englishText = `Error: ${error}`;
        
        const text = this.currentLanguage.includes('ur') ? urduText : englishText;
        
        return this.speak(text, {
            rate: 0.8,
            pitch: 0.9,
            language: this.currentLanguage
        });
    }

    // ============ UTILITY METHODS ============
    
    getVoiceInfo() {
        return {
            isSupported: this.isSupported,
            isListening: this.isListening,
            currentLanguage: this.currentLanguage,
            availableVoices: this.voices.length,
            isSpeaking: this.synthesis ? this.synthesis.speaking : false
        };
    }

    testVoice(text = null) {
        const testText = text || (
            this.currentLanguage.includes('ur') 
                ? 'یہ Red Dot Pharmacy کا آواز ٹیسٹ ہے۔'
                : 'This is a voice test from Red Dot Pharmacy.'
        );
        
        return this.speak(testText);
    }

    // ============ CLEANUP ============
    
    cleanup() {
        this.stopListening();
        this.stopSpeaking();
        
        if (this.recognition) {
            this.recognition = null;
        }
    }
}

// Global voice assistant instance
let voiceAssistant = null;

// Initialize voice assistant
function initializeVoiceAssistant() {
    try {
        voiceAssistant = new VoiceAssistant();
        
        // Setup common voice commands for the pharmacy
        const commonCommands = {
            'search medicine': 'searchMedicines',
            'book appointment': () => scrollToSection('consultation'),
            'show cart': 'showCart',
            'help': () => {
                const helpText = voiceAssistant.currentLanguage.includes('ur') 
                    ? 'آپ دوا تلاش کرنے، ملاقات بک کرنے، یا ٹوکری دیکھنے کے لیے آواز استعمال کر سکتے ہیں۔'
                    : 'You can use voice to search medicines, book appointments, or view your cart.';
                voiceAssistant.speak(helpText);
            },
            'medicine information': (transcript) => {
                // Extract medicine name from transcript and speak its info
                // This would be enhanced with NLP in production
                console.log('Medicine info requested for:', transcript);
            }
        };
        
        voiceAssistant.setupVoiceCommands(commonCommands);
        
        console.log('Voice Assistant initialized successfully');
        return voiceAssistant;
        
    } catch (error) {
        console.error('Failed to initialize voice assistant:', error);
        return null;
    }
}

// Global functions for integration with other components
function startVoiceRecognition(options = {}) {
    if (voiceAssistant) {
        return voiceAssistant.startListening(options);
    }
    throw new Error('Voice assistant not initialized');
}

function stopVoiceRecognition() {
    if (voiceAssistant) {
        voiceAssistant.stopListening();
    }
}

function speakText(text, options = {}) {
    if (voiceAssistant) {
        return voiceAssistant.speak(text, options);
    }
    throw new Error('Voice assistant not initialized');
}

function setVoiceLanguage(language) {
    if (voiceAssistant) {
        return voiceAssistant.setLanguage(language);
    }
    return false;
}

function getVoiceStatus() {
    if (voiceAssistant) {
        return voiceAssistant.getVoiceInfo();
    }
    return null;
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (voiceAssistant) {
        voiceAssistant.cleanup();
    }
});

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeVoiceAssistant);
