// Complete auth.js - Fixed all logical issues + RAG integration
console.log('Auth.js loaded');

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = JSON.parse(localStorage.getItem('user_info') || 'null');
        console.log('AuthManager initialized:', { token: !!this.token, user: this.user });
    }

    saveAuthInfo(token, user) {
        console.log('Saving authentication information:', { token: !!token, user });
        this.token = token;
        this.user = user;
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_info', JSON.stringify(user));
    }

    clearAuthInfo() {
        console.log('Clearing authentication information');
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
    }

    isLoggedIn() {
        const loggedIn = !!this.token;
        console.log('Checking login status:', loggedIn);
        return loggedIn;
    }

    getAuthHeaders() {
        if (!this.token) return {};
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }

    async verifyToken() {
        if (!this.token) {
            console.log('No token, verification failed');
            return false;
        }

        try {
            console.log('Verifying token...');
            const response = await fetch('/api/v1/auth/verify', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (response.status === 401) {
                console.log('Invalid token, clearing authentication information');
                this.clearAuthInfo();
                return false;
            }

            const result = await response.json();
            console.log('Token verification result:', result);

            if (result.valid) {
                if (result.user) {
                    this.user = result.user;
                    localStorage.setItem('user_info', JSON.stringify(result.user));
                }
                return true;
            } else {
                console.log('Token verification failed:', result.error);
                this.clearAuthInfo();
                return false;
            }
        } catch (error) {
            console.error('Error verifying token:', error);
            return false;
        }
    }

    async logout() {
        console.log('Performing logout');
        try {
            await fetch('/api/v1/auth/logout', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });
        } catch (error) {
            console.error('Logout request failed:', error);
        } finally {
            this.clearAuthInfo();
            window.location.href = '/';
        }
    }
}

// Create global instance
const authManager = new AuthManager();

// Authenticated fetch helper function
async function authenticatedFetch(url, options = {}) {
    if (!authManager.isLoggedIn()) {
        alert('Please log in first');
        window.location.href = '/api/v1/auth/login';
        return null;
    }

    const headers = {
        ...authManager.getAuthHeaders(),
        ...options.headers
    };

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            console.log('Token expired, clearing login information');
            authManager.clearAuthInfo();
            alert('Login expired, please log in again');
            window.location.href = '/api/v1/auth/login';
            return null;
        }

        return response;
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// ===== UI UPDATE FUNCTIONS =====
function updateUIForLoggedInUser() {
    console.log('Updating UI for logged-in state');

    const authButtons = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');
    const welcomeText = document.getElementById('welcomeText');

    console.log('Elements found:', {
        authButtons: !!authButtons,
        userInfo: !!userInfo,
        welcomeText: !!welcomeText
    });

    if (authButtons) {
        authButtons.style.display = 'none';
        console.log('Hiding login buttons');
    }

    if (userInfo) {
        userInfo.style.display = 'flex';
        console.log('Displaying user info');
    }

    if (welcomeText && authManager.user) {
        welcomeText.textContent = `Welcome, ${authManager.user.username}`;
        console.log('Updating welcome text:', `Welcome, ${authManager.user.username}`);
    }
}

function updateUIForLoggedOutUser() {
    console.log('Updating UI for logged-out state');

    const authButtons = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');

    if (authButtons) {
        authButtons.style.display = 'flex';
        console.log('Displaying login buttons');
    }

    if (userInfo) {
        userInfo.style.display = 'none';
        console.log('Hiding user info');
    }
}

// ===== FORM HANDLING =====
function bindAuthForms() {
    console.log('Binding form events');

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        console.log('Binding registration form');
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
        console.log('Binding login form');
    }
}

async function handleLogin(event) {
    console.log('Handling login form submission');
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };

    console.log('Login data:', { username: data.username, password: '***' });

    if (!data.username || !data.password) {
        showMessage('Please enter username and password', 'error');
        return;
    }

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Logging in...';
    submitBtn.disabled = true;

    try {
        console.log('Sending login request...');
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        console.log('Login response status:', response.status);

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Response is not JSON format:', text);
            showMessage('Server response format error', 'error');
            return;
        }

        const result = await response.json();
        console.log('Login response data:', result);

        if (result.success && result.token) {
            console.log('Login successful, saving authentication information');
            authManager.saveAuthInfo(result.token, {
                user_id: result.user_id,
                username: result.username
            });

            showMessage('Login successful! Redirecting...', 'success');

            setTimeout(() => {
                console.log('Redirecting to homepage');
                window.location.href = '/';
            }, 1500);
        } else {
            console.log('Login failed:', result.error);
            showMessage('Login failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Network error, please try again later', 'error');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

async function handleRegister(event) {
    console.log('Handling registration form submission');
    event.preventDefault();

    const formData = new FormData(event.target);
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');

    if (password !== confirmPassword) {
        showMessage('Passwords do not match', 'error');
        return;
    }

    if (password.length < 6) {
        showMessage('Password must be at least 6 characters long', 'error');
        return;
    }

    const data = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: password
    };

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Registering...';
    submitBtn.disabled = true;

    try {
        const response = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showMessage('Registration successful! Redirecting to login page...', 'success');
            setTimeout(() => {
                window.location.href = '/api/v1/auth/login';
            }, 1500);
        } else {
            showMessage('Registration failed: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('Network error, please try again later', 'error');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

function showMessage(text, type = 'info') {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';

        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    } else {
        console.log(`Message (${type}):`, text);
        if (type === 'error') {
            alert(text);
        }
    }
}

// ===== PAGE NAVIGATION FUNCTIONS =====
function goToTopCompanies() {
    window.location.href = '/stocks.html';
}

function goToCompare() {
    window.location.href = '/compare.html';
}

function goToForum() {
    if (!authManager.isLoggedIn()) {
        alert('Please log in to access the forum.');
        window.location.href = '/api/v1/auth/login';
        return;
    }
    window.location.href = '/api/v1/forum/forum.html';
}

// ===== CHATBOX FUNCTIONALITY =====
let chatboxOpen = false;

function toggleChatbox() {
    const chatbox = document.getElementById('chatboxContainer');
    const toggle = document.getElementById('chatToggle');

    if (!chatbox || !toggle) return; // Return if chatbox elements are not present

    chatboxOpen = !chatboxOpen;

    if (chatboxOpen) {
        chatbox.classList.add('active');
        toggle.style.display = 'none';
        setTimeout(() => {
            const input = document.getElementById('chatInput');
            if (input) input.focus();
        }, 300);
    } else {
        chatbox.classList.remove('active');
        toggle.style.display = 'flex';
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// ===== RAG CHATBOX INTEGRATION - Fixed Version =====
// RAG server configuration
const RAG_CONFIG = {
    baseUrl: 'http://127.0.0.1:5001',
    timeout: 30000,
    retryAttempts: 2
};

// Connection status tracking
let ragServerStatus = 'unknown'; // 'online', 'offline', 'unknown'

// Check RAG server status
async function checkRAGServerStatus() {
    try {
        console.log('🔍 Checking RAG server status...');

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${RAG_CONFIG.baseUrl}/health`, {
            method: 'GET',
            signal: controller.signal,
            mode: 'cors'
        });

        clearTimeout(timeoutId);

        if (response.ok) {
            const data = await response.json();
            console.log('✅ RAG server online:', data);
            ragServerStatus = 'online';
            return true;
        } else {
            console.log('❌ RAG server responded abnormally:', response.status);
            ragServerStatus = 'offline';
            return false;
        }
    } catch (error) {
        console.log('❌ RAG server connection failed:', error.message);
        ragServerStatus = 'offline';
        return false;
    }
}

// Fetch with retry mechanism
async function fetchWithRetry(url, options, retries = RAG_CONFIG.retryAttempts) {
    for (let i = 0; i < retries; i++) {
        try {
            console.log(`🔄 Request attempt ${i + 1}/${retries}: ${url}`);

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), RAG_CONFIG.timeout);

            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response;

        } catch (error) {
            console.log(`❌ Request failed ${i + 1}/${retries}:`, error.message);

            if (i === retries - 1) {
                throw error; // Throw error on last attempt failure
            }

            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}

// Fixed sendMessage function
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    try {
        console.log('🤖 Sending query to RAG system:', message);

        // 🔧 Use enhanced fetch request
        const response = await fetchWithRetry(`${RAG_CONFIG.baseUrl}/bot`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({query: message}),
            mode: 'cors'
        });

        console.log('📡 Response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Check response type
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('❌ Response is not JSON format:', text);
            throw new Error('Server response format error');
        }

        const result = await response.json();
        console.log('🤖 RAG response:', result);

        hideTypingIndicator();
        ragServerStatus = 'online'; // Update status

        if (result.response) {
            addMessage(result.response, 'bot');
        } else if (result.error) {
            addMessage(`Sorry, an error occurred while processing your question: ${result.error}`, 'bot');
        } else {
            addMessage('Sorry, I cannot answer your question at the moment.', 'bot');
        }

    } catch (error) {
        console.error('💥 Chat error:', error);
        hideTypingIndicator();
        ragServerStatus = 'offline'; // Update status

        let errorMessage = '🔌 Could not connect to AI server.';

        if (error.name === 'AbortError') {
            errorMessage += '\n⏱️ Request timed out, please try again later.';
        } else if (error.message.includes('Failed to fetch') ||
                   error.message.includes('ERR_CONNECTION_REFUSED')) {
            errorMessage += '\n❌ Connection refused. Please ensure:';
            errorMessage += '\n• The RAG server is running (python api_server.py)';
            errorMessage += '\n• The server address is: http://127.0.0.1:5001';
            errorMessage += '\n• Check firewall settings';
        } else if (error.message.includes('CORS')) {
            errorMessage += '\n🚫 Cross-Origin Request Blocked.';
        } else {
            errorMessage += `\n🐛 Error: ${error.message}`;
        }

        addMessage(errorMessage, 'bot');

        // Provide debugging suggestions
        setTimeout(() => {
            addMessage('💡 Debugging tips:\n1. Visit: http://127.0.0.1:5001/health in your browser\n2. Confirm the RAG server console shows "RAG API is running"\n3. Check the Network tab in developer tools', 'bot');
        }, 1000);
    }
}

// Improved message display function
function addMessage(message, sender) {
    const messagesContainer = document.getElementById('chatboxMessages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbox-message ${sender}`;

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    // Handle multi-line text and line breaks
    if (message.includes('\n')) {
        const lines = message.split('\n');
        lines.forEach((line, index) => {
            if (index > 0) {
                bubble.appendChild(document.createElement('br'));
            }
            bubble.appendChild(document.createTextNode(line));
        });
    } else {
        bubble.textContent = message;
    }

    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatboxMessages');
    if (!messagesContainer) return;

    // Remove existing indicator
    hideTypingIndicator();

    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typingIndicator';

    typingDiv.innerHTML = `
        <span>AI is thinking</span>
        <div class="typing-dots">
            <div></div>
            <div></div>
            <div></div>
        </div>
    `;

    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Debugging functions
function testRAGConnection() {
    console.log('🧪 Testing RAG connection...');
    checkRAGServerStatus().then(isOnline => {
        if (isOnline) {
            addMessage('✅ RAG server connection test successful!', 'bot');
        } else {
            addMessage('❌ RAG server connection test failed', 'bot');
        }
    });
}

// Expose to global scope for debugging
window.testRAGConnection = testRAGConnection;
window.checkRAGServerStatus = checkRAGServerStatus;

// ===== MAIN INITIALIZATION =====
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Page DOMContentLoaded event triggered');

    // Check if the page requires authentication
    const requireAuth = document.body.dataset.requireAuth === 'true';
    console.log('Page requires authentication:', requireAuth);

    if (requireAuth && !authManager.isLoggedIn()) {
        console.log('Page requires authentication but user is not logged in');
        alert('Please log in first');
        window.location.href = '/api/v1/auth/login';
        return;
    }

    // Login status check and UI update
    if (authManager.isLoggedIn()) {
        console.log('User is logged in, verifying token...');
        const isValid = await authManager.verifyToken();
        if (isValid) {
            updateUIForLoggedInUser();
        } else {
            updateUIForLoggedOutUser();
        }
    } else {
        console.log('User is not logged in');
        updateUIForLoggedOutUser();
    }

    // Bind form events
    bindAuthForms();

    // Initialize chatbox (if present)
    const chatboxContainer = document.getElementById('chatboxContainer');
    if (chatboxContainer) {
        console.log('🚀 Initializing chatbox...');

        // Initialize chatbox (if present)
        setTimeout(async () => {
            const isOnline = await checkRAGServerStatus();
            if (isOnline) {
                // Only show welcome message once, not repeatedly
                const existingMessages = document.querySelectorAll('.chatbox-message');
                if (existingMessages.length === 0) {
                    addMessage('👋 Hi! I\'m your investment assistant. I can help you analyze company information, stock data, and more. How can I assist you today?', 'bot');
                }
            } else {
                addMessage('⚠️ AI server is currently offline. Please ensure the RAG server is running and refresh the page to retry.', 'bot');
            }
        }, 1000);
    }

    // Close chatbox on outside click
    document.addEventListener('click', function(event) {
        const chatbox = document.getElementById('chatboxContainer');
        const toggle = document.getElementById('chatToggle');

        if (chatbox && toggle && chatboxOpen &&
            !chatbox.contains(event.target) &&
            !toggle.contains(event.target)) {
            toggleChatbox();
        }
    });

    // Prevent closing when clicking inside chatbox
    if (chatboxContainer) {
        chatboxContainer.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }
});