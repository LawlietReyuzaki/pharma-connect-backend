// Red Dot Pharmacy - Chatbot with Urdu Support and Medical Guardrails
// Handles text and voice chat interactions with medical safety features

class RedDotChatbot {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.isVoiceActive = false;
        this.preferUrdu = true;
        this.messageHistory = [];
        this.isExpanded = false;
        
        this.initializeChatbot();
        this.setupEventListeners();
    }

    // ============ INITIALIZATION ============
    
    initializeChatbot() {
        const chatWidget = document.getElementById('chatWidget');
        if (!chatWidget) return;

        // Load chat history if available
        this.loadChatHistory();
        
        // Initialize expanded state
        this.updateChatWidgetState();
    }

    setupEventListeners() {
        // Chat toggle
        const chatHeader = document.querySelector('.chat-header');
        if (chatHeader) {
            chatHeader.addEventListener('click', () => this.toggleChat());
        }

        // Message input
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Voice button
        const voiceButton = document.getElementById('voiceButton');
        if (voiceButton) {
            voiceButton.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent chat toggle
                this.toggleVoiceInput();
            });
        }
    }

    generateSessionId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // ============ CHAT UI MANAGEMENT ============
    
    toggleChat() {
        this.isExpanded = !this.isExpanded;
        this.updateChatWidgetState();
    }

    updateChatWidgetState() {
        const chatWidget = document.getElementById('chatWidget');
        const chatToggle = document.querySelector('.chat-toggle');
        
        if (this.isExpanded) {
            chatWidget?.classList.add('expanded');
            if (chatToggle) chatToggle.style.transform = 'rotate(180deg)';
        } else {
            chatWidget?.classList.remove('expanded');
            if (chatToggle) chatToggle.style.transform = 'rotate(0deg)';
        }
    }

    // ============ MESSAGE HANDLING ============
    
    async sendMessage(messageText = null) {
        const input = document.getElementById('chatInput');
        const message = messageText || input?.value?.trim();
        
        if (!message) return;

        // Clear input
        if (input) input.value = '';

        // Add user message to chat
        this.addMessageToChat('user', message);

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send to chatbot API
            const response = await this.sendToChatbotAPI(message);
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Add bot response
            this.addMessageToChat('bot', response.message, response);
            
            // Handle special responses
            if (response.flagged) {
                this.handleFlaggedMessage(response);
            }
            
            if (response.needs_doctor) {
                this.showDoctorRecommendation();
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('bot', 'معذرت، میں فی الوقت دستیاب نہیں ہوں۔ براہ کرم بعد میں کوشش کریں۔\nSorry, I\'m not available right now. Please try again later.');
        }
    }

    async sendToChatbotAPI(message) {
        const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
        
        const requestData = {
            text: message,
            session_id: this.sessionId,
            prefer_urdu: this.preferUrdu,
            user_id: userData.id || null
        };

        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error('Chatbot API error');
        }

        return await response.json();
    }

    addMessageToChat(sender, message, metadata = {}) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(message)}
                <small class="text-muted d-block mt-1">${timestamp}</small>
                ${metadata.flagged ? '<small class="text-danger d-block"><i class="fas fa-exclamation-triangle me-1"></i>Medical Alert</small>' : ''}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Store in history
        this.messageHistory.push({
            sender,
            message,
            timestamp: new Date().toISOString(),
            metadata
        });

        // Save to localStorage
        this.saveChatHistory();

        // Announce message for accessibility
        if (sender === 'bot') {
            this.announceMessage(message);
        }
    }

    formatMessage(message) {
        // Convert line breaks to <br> tags
        return message.replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot-message typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // ============ VOICE FUNCTIONALITY ============
    
    toggleVoiceInput() {
        if (this.isVoiceActive) {
            this.stopVoiceInput();
        } else {
            this.startVoiceInput();
        }
    }

    startVoiceInput() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            this.showVoiceError('Speech recognition is not supported in this browser.');
            return;
        }

        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.lang = this.preferUrdu ? 'ur-PK' : 'en-US';
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.maxAlternatives = 1;

            this.recognition.onstart = () => {
                this.isVoiceActive = true;
                this.updateVoiceUI(true);
                this.showVoiceStatus('Listening... / سن رہا ہوں...');
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.handleVoiceResult(transcript);
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.stopVoiceInput();
                this.showVoiceError('Voice recognition error. Please try again.');
            };

            this.recognition.onend = () => {
                this.stopVoiceInput();
            };

            this.recognition.start();
            
        } catch (error) {
            console.error('Voice input error:', error);
            this.showVoiceError('Failed to start voice input.');
        }
    }

    stopVoiceInput() {
        if (this.recognition) {
            this.recognition.stop();
        }
        
        this.isVoiceActive = false;
        this.updateVoiceUI(false);
        this.hideVoiceStatus();
    }

    async handleVoiceResult(transcript) {
        try {
            // Add transcript to input field
            const input = document.getElementById('chatInput');
            if (input) {
                input.value = transcript;
            }

            // Send voice message to API
            const response = await this.sendVoiceToChatbotAPI(transcript);
            
            // Add messages to chat
            this.addMessageToChat('user', `🎤 ${transcript}`);
            this.addMessageToChat('bot', response.message, response);
            
            // Speak the response if it's in Urdu or contains Urdu text
            if (response.message && this.preferUrdu) {
                this.speakResponse(response.message);
            }
            
            // Handle special responses
            if (response.flagged) {
                this.handleFlaggedMessage(response);
            }
            
        } catch (error) {
            console.error('Voice message error:', error);
            this.addMessageToChat('bot', 'Voice message processing failed. Please try typing your message.');
        }
    }

    async sendVoiceToChatbotAPI(transcript) {
        const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
        
        const requestData = {
            transcript: transcript,
            session_id: this.sessionId,
            prefer_urdu: this.preferUrdu,
            user_id: userData.id || null
        };

        const response = await fetch('/api/chat/voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error('Voice chatbot API error');
        }

        return await response.json();
    }

    speakResponse(text) {
        if (!('speechSynthesis' in window)) {
            console.warn('Text-to-speech not supported');
            return;
        }

        try {
            // Cancel any ongoing speech
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = this.preferUrdu ? 'ur-PK' : 'en-US';
            utterance.rate = 0.8;
            utterance.pitch = 1;
            utterance.volume = 0.8;

            // Find appropriate voice
            const voices = speechSynthesis.getVoices();
            const urduVoice = voices.find(voice => voice.lang.includes('ur'));
            const englishVoice = voices.find(voice => voice.lang.includes('en-US'));
            
            if (this.preferUrdu && urduVoice) {
                utterance.voice = urduVoice;
            } else if (englishVoice) {
                utterance.voice = englishVoice;
            }

            speechSynthesis.speak(utterance);
            
        } catch (error) {
            console.error('Text-to-speech error:', error);
        }
    }

    updateVoiceUI(isActive) {
        const voiceButton = document.getElementById('voiceButton');
        const voiceIcon = voiceButton?.querySelector('i');
        
        if (isActive) {
            voiceButton?.classList.add('btn-danger');
            voiceButton?.classList.remove('btn-light');
            voiceIcon?.classList.replace('fa-microphone', 'fa-stop');
        } else {
            voiceButton?.classList.add('btn-light');
            voiceButton?.classList.remove('btn-danger');
            voiceIcon?.classList.replace('fa-stop', 'fa-microphone');
        }
    }

    showVoiceStatus(message) {
        const voiceStatus = document.getElementById('voiceStatus');
        if (voiceStatus) {
            voiceStatus.textContent = message;
            voiceStatus.style.display = 'block';
        }
    }

    hideVoiceStatus() {
        const voiceStatus = document.getElementById('voiceStatus');
        if (voiceStatus) {
            voiceStatus.style.display = 'none';
        }
    }

    showVoiceError(message) {
        this.addMessageToChat('bot', `🎤 ${message}`);
    }

    // ============ MEDICAL SAFETY FEATURES ============
    
    handleFlaggedMessage(response) {
        // Add visual indicator for flagged messages
        const lastMessage = document.querySelector('.chat-message:last-child .message-content');
        if (lastMessage) {
            lastMessage.classList.add('flagged-message');
        }

        // Show emergency information
        this.showEmergencyInfo();
    }

    showEmergencyInfo() {
        const emergencyDiv = document.createElement('div');
        emergencyDiv.className = 'chat-message bot-message emergency-message';
        emergencyDiv.innerHTML = `
            <div class="message-content bg-danger text-white">
                <strong>🚨 ہنگامی معلومات / Emergency Information</strong><br>
                <p class="mb-2">اگر یہ طبی ہنگامی صورتحال ہے تو:</p>
                <p class="mb-2">If this is a medical emergency:</p>
                <div class="d-flex gap-2 mb-2">
                    <a href="tel:1122" class="btn btn-light btn-sm">
                        <i class="fas fa-phone me-1"></i>1122
                    </a>
                    <a href="tel:+92515111222" class="btn btn-light btn-sm">
                        <i class="fas fa-hospital me-1"></i>Red Dot Pharmacy
                    </a>
                </div>
                <small>فوری طور پر قریبی ہسپتال جائیں یا ایمرجنسی سروس سے رابطہ کریں</small>
            </div>
        `;

        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.appendChild(emergencyDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    showDoctorRecommendation() {
        const recommendationDiv = document.createElement('div');
        recommendationDiv.className = 'chat-message bot-message doctor-recommendation';
        recommendationDiv.innerHTML = `
            <div class="message-content bg-info text-white">
                <strong>👨‍⚕️ ڈاکٹر سے مشورہ / Doctor Consultation</strong><br>
                <p class="mb-2">بہتر تشخیص کے لیے ہمارے ڈاکٹرز سے آن لائن مشورہ کریں</p>
                <p class="mb-2">For better diagnosis, consult with our doctors online</p>
                <button class="btn btn-light btn-sm" onclick="scrollToSection('consultation')">
                    <i class="fas fa-video me-1"></i>Book Consultation
                </button>
            </div>
        `;

        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.appendChild(recommendationDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // ============ CHAT HISTORY MANAGEMENT ============
    
    saveChatHistory() {
        try {
            const historyKey = `chat_history_${this.sessionId}`;
            localStorage.setItem(historyKey, JSON.stringify(this.messageHistory));
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }

    loadChatHistory() {
        try {
            const historyKey = `chat_history_${this.sessionId}`;
            const saved = localStorage.getItem(historyKey);
            
            if (saved) {
                this.messageHistory = JSON.parse(saved);
                this.restoreChatMessages();
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    restoreChatMessages() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        // Clear existing messages except the welcome message
        const welcomeMessage = messagesContainer.querySelector('.bot-message');
        messagesContainer.innerHTML = '';
        
        if (welcomeMessage) {
            messagesContainer.appendChild(welcomeMessage);
        }

        // Restore saved messages
        this.messageHistory.forEach(msg => {
            if (msg.sender && msg.message) {
                this.addMessageToChat(msg.sender, msg.message, msg.metadata || {});
            }
        });
    }

    clearChatHistory() {
        this.messageHistory = [];
        const historyKey = `chat_history_${this.sessionId}`;
        localStorage.removeItem(historyKey);
        
        // Clear UI
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="bot-message">
                    <div class="message-content">
                        <p>سلام! میں Red Dot Pharmacy کا مددگار ہوں۔ آپ کی صحت کے بارے میں سوال پوچھ سکتے ہیں۔</p>
                        <p class="small">Hello! I'm Red Dot Pharmacy's assistant. You can ask questions about your health.</p>
                    </div>
                </div>
            `;
        }
    }

    // ============ ACCESSIBILITY FEATURES ============
    
    announceMessage(message) {
        // Create announcement for screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Chatbot response: ${message}`;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    // ============ LANGUAGE TOGGLE ============
    
    toggleLanguage() {
        this.preferUrdu = !this.preferUrdu;
        
        // Update UI to reflect language preference
        const chatHeader = document.querySelector('.chat-header');
        if (chatHeader) {
            if (this.preferUrdu) {
                chatHeader.innerHTML = `
                    <i class="fas fa-comments"></i>
                    <span>Ask Our Assistant</span>
                    <span class="urdu-text">اردو میں پوچھیں</span>
                    <i class="fas fa-chevron-down chat-toggle"></i>
                `;
            } else {
                chatHeader.innerHTML = `
                    <i class="fas fa-comments"></i>
                    <span>Health Assistant</span>
                    <span class="urdu-text">English</span>
                    <i class="fas fa-chevron-down chat-toggle"></i>
                `;
            }
        }
        
        // Update input placeholder
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.placeholder = this.preferUrdu 
                ? 'اپنا پیغام لکھیں...' 
                : 'Type your message...';
        }
    }

    // ============ EXTERNAL INTEGRATION ============
    
    async getSuggestedMedicines(symptoms) {
        try {
            const response = await fetch('/api/store/search', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.results || [];
            }
        } catch (error) {
            console.error('Error fetching medicine suggestions:', error);
        }
        
        return [];
    }
}

// Global functions for HTML onclick handlers
function sendMessage() {
    if (window.chatbot) {
        window.chatbot.sendMessage();
    }
}

function toggleVoiceInput() {
    if (window.chatbot) {
        window.chatbot.toggleVoiceInput();
    }
}

function toggleChat() {
    if (window.chatbot) {
        window.chatbot.toggleChat();
    }
}

// Initialize chatbot when DOM is loaded
function initializeChatbot() {
    window.chatbot = new RedDotChatbot();
}

// Add CSS for typing indicator animation
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    
    .typing-dots span {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        background-color: #6c757d;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    .flagged-message {
        border-left: 4px solid #dc3545 !important;
        background: rgba(220, 53, 69, 0.1) !important;
    }
    
    .emergency-message .message-content {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
    }
`;
document.head.appendChild(style);
