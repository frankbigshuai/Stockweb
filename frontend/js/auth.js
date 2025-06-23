// 完整的 auth.js - 修复所有逻辑问题 + RAG集成
console.log('Auth.js 加载完成');

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = JSON.parse(localStorage.getItem('user_info') || 'null');
        console.log('AuthManager初始化:', { token: !!this.token, user: this.user });
    }

    saveAuthInfo(token, user) {
        console.log('保存认证信息:', { token: !!token, user });
        this.token = token;
        this.user = user;
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_info', JSON.stringify(user));
    }

    clearAuthInfo() {
        console.log('清除认证信息');
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
    }

    isLoggedIn() {
        const loggedIn = !!this.token;
        console.log('检查登录状态:', loggedIn);
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
            console.log('没有token，验证失败');
            return false;
        }

        try {
            console.log('验证token...');
            const response = await fetch('/api/v1/auth/verify', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (response.status === 401) {
                console.log('Token无效，清除认证信息');
                this.clearAuthInfo();
                return false;
            }

            const result = await response.json();
            console.log('Token验证结果:', result);

            if (result.valid) {
                if (result.user) {
                    this.user = result.user;
                    localStorage.setItem('user_info', JSON.stringify(result.user));
                }
                return true;
            } else {
                console.log('Token验证失败:', result.error);
                this.clearAuthInfo();
                return false;
            }
        } catch (error) {
            console.error('Token验证出错:', error);
            return false;
        }
    }

    async logout() {
        console.log('执行登出');
        try {
            await fetch('/api/v1/auth/logout', {
                method: 'POST',
                headers: this.getAuthHeaders()
            });
        } catch (error) {
            console.error('登出请求失败:', error);
        } finally {
            this.clearAuthInfo();
            window.location.href = '/';
        }
    }
}

// 创建全局实例
const authManager = new AuthManager();

// 认证请求辅助函数
async function authenticatedFetch(url, options = {}) {
    if (!authManager.isLoggedIn()) {
        alert('请先登录');
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
            console.log('Token已过期，清除登录信息');
            authManager.clearAuthInfo();
            alert('登录已过期，请重新登录');
            window.location.href = '/api/v1/auth/login';
            return null;
        }

        return response;
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

// ===== UI UPDATE FUNCTIONS =====
function updateUIForLoggedInUser() {
    console.log('更新UI为登录状态');
    
    const authButtons = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');
    const welcomeText = document.getElementById('welcomeText');
    
    console.log('找到的元素:', { 
        authButtons: !!authButtons, 
        userInfo: !!userInfo, 
        welcomeText: !!welcomeText 
    });
    
    if (authButtons) {
        authButtons.style.display = 'none';
        console.log('隐藏登录按钮');
    }
    
    if (userInfo) {
        userInfo.style.display = 'flex';
        console.log('显示用户信息');
    }
    
    if (welcomeText && authManager.user) {
        welcomeText.textContent = `Welcome, ${authManager.user.username}`;
        console.log('更新欢迎文字:', `Welcome, ${authManager.user.username}`);
    }
}

function updateUIForLoggedOutUser() {
    console.log('更新UI为未登录状态');
    
    const authButtons = document.getElementById('authButtons');
    const userInfo = document.getElementById('userInfo');
    
    if (authButtons) {
        authButtons.style.display = 'flex';
        console.log('显示登录按钮');
    }
    
    if (userInfo) {
        userInfo.style.display = 'none';
        console.log('隐藏用户信息');
    }
}

// ===== FORM HANDLING =====
function bindAuthForms() {
    console.log('绑定表单事件');
    
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        console.log('绑定注册表单');
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
        console.log('绑定登录表单');
    }
}

async function handleLogin(event) {
    console.log('处理登录表单提交');
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    console.log('登录数据:', { username: data.username, password: '***' });
    
    if (!data.username || !data.password) {
        showMessage('请输入用户名和密码', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '登录中...';
    submitBtn.disabled = true;
    
    try {
        console.log('发送登录请求...');
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        console.log('登录响应状态:', response.status);
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('响应不是JSON格式:', text);
            showMessage('服务器响应格式错误', 'error');
            return;
        }
        
        const result = await response.json();
        console.log('登录响应数据:', result);
        
        if (result.success && result.token) {
            console.log('登录成功，保存认证信息');
            authManager.saveAuthInfo(result.token, {
                user_id: result.user_id,
                username: result.username
            });
            
            showMessage('登录成功！即将跳转...', 'success');
            
            setTimeout(() => {
                console.log('跳转到首页');
                window.location.href = '/';
            }, 1500);
        } else {
            console.log('登录失败:', result.error);
            showMessage('登录失败: ' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('登录错误:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

async function handleRegister(event) {
    console.log('处理注册表单提交');
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    
    if (password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('密码长度至少6位', 'error');
        return;
    }
    
    const data = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: password
    };
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '注册中...';
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
            showMessage('注册成功！即将跳转到登录页面...', 'success');
            setTimeout(() => {
                window.location.href = '/api/v1/auth/login';
            }, 1500);
        } else {
            showMessage('注册失败: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('注册错误:', error);
        showMessage('网络错误，请稍后重试', 'error');
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
    
    if (!chatbox || !toggle) return; // 如果页面没有聊天框，直接返回
    
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

// ===== RAG CHATBOX INTEGRATION - 修复版本 =====
// RAG服务器配置
const RAG_CONFIG = {
    baseUrl: 'http://127.0.0.1:5001',
    timeout: 30000,
    retryAttempts: 2
};

// 连接状态追踪
let ragServerStatus = 'unknown'; // 'online', 'offline', 'unknown'

// 检查RAG服务器状态
async function checkRAGServerStatus() {
    try {
        console.log('🔍 检查RAG服务器状态...');
        
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
            console.log('✅ RAG服务器在线:', data);
            ragServerStatus = 'online';
            return true;
        } else {
            console.log('❌ RAG服务器响应异常:', response.status);
            ragServerStatus = 'offline';
            return false;
        }
    } catch (error) {
        console.log('❌ RAG服务器连接失败:', error.message);
        ragServerStatus = 'offline';
        return false;
    }
}

// 带重试机制的fetch
async function fetchWithRetry(url, options, retries = RAG_CONFIG.retryAttempts) {
    for (let i = 0; i < retries; i++) {
        try {
            console.log(`🔄 请求尝试 ${i + 1}/${retries}: ${url}`);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), RAG_CONFIG.timeout);
            
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            return response;
            
        } catch (error) {
            console.log(`❌ 请求失败 ${i + 1}/${retries}:`, error.message);
            
            if (i === retries - 1) {
                throw error; // 最后一次尝试失败，抛出错误
            }
            
            // 等待后重试
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}

// 修复的sendMessage函数
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 添加用户消息到界面
    addMessage(message, 'user');
    input.value = '';
    
    // 显示打字指示器
    showTypingIndicator();
    
    try {
        console.log('🤖 发送查询到RAG系统:', message);
        
        // 🔧 使用增强的fetch请求
        const response = await fetchWithRetry(`${RAG_CONFIG.baseUrl}/bot`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({query: message}),
            mode: 'cors'
        });
        
        console.log('📡 响应状态:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // 检查响应类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('❌ 响应不是JSON格式:', text);
            throw new Error('服务器响应格式错误');
        }
        
        const result = await response.json();
        console.log('🤖 RAG响应:', result);
        
        hideTypingIndicator();
        ragServerStatus = 'online'; // 更新状态
        
        if (result.response) {
            addMessage(result.response, 'bot');
        } else if (result.error) {
            addMessage(`抱歉，处理您的问题时出现错误：${result.error}`, 'bot');
        } else {
            addMessage('抱歉，我现在无法回答您的问题。', 'bot');
        }
        
    } catch (error) {
        console.error('💥 聊天错误:', error);
        hideTypingIndicator();
        ragServerStatus = 'offline'; // 更新状态
        
        let errorMessage = '🔌 无法连接到AI服务器。';
        
        if (error.name === 'AbortError') {
            errorMessage += '\n⏱️ 请求超时，请稍后重试。';
        } else if (error.message.includes('Failed to fetch') || 
                   error.message.includes('ERR_CONNECTION_REFUSED')) {
            errorMessage += '\n❌ 连接被拒绝。请确保：';
            errorMessage += '\n• RAG服务器正在运行 (python api_server.py)';
            errorMessage += '\n• 服务器地址：http://127.0.0.1:5001';
            errorMessage += '\n• 检查防火墙设置';
        } else if (error.message.includes('CORS')) {
            errorMessage += '\n🚫 跨域请求被阻止。';
        } else {
            errorMessage += `\n🐛 错误：${error.message}`;
        }
        
        addMessage(errorMessage, 'bot');
        
        // 提供调试建议
        setTimeout(() => {
            addMessage('💡 调试建议：\n1. 在浏览器中访问：http://127.0.0.1:5001/health\n2. 确认RAG服务器控制台显示"RAG API is running"\n3. 检查开发者工具的Network标签页', 'bot');
        }, 1000);
    }
}

// 改进的消息显示函数
function addMessage(message, sender) {
    const messagesContainer = document.getElementById('chatboxMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbox-message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // 处理多行文本和换行
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
    
    // 滚动到底部
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatboxMessages');
    if (!messagesContainer) return;
    
    // 移除现有的指示器
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

// 调试函数
function testRAGConnection() {
    console.log('🧪 测试RAG连接...');
    checkRAGServerStatus().then(isOnline => {
        if (isOnline) {
            addMessage('✅ RAG服务器连接测试成功！', 'bot');
        } else {
            addMessage('❌ RAG服务器连接测试失败', 'bot');
        }
    });
}

// 暴露给全局作用域用于调试
window.testRAGConnection = testRAGConnection;
window.checkRAGServerStatus = checkRAGServerStatus;

// ===== MAIN INITIALIZATION =====
document.addEventListener('DOMContentLoaded', async function() {
    console.log('页面DOMContentLoaded事件触发');
    
    // 检查是否在需要认证的页面
    const requireAuth = document.body.dataset.requireAuth === 'true';
    console.log('页面是否需要认证:', requireAuth);
    
    if (requireAuth && !authManager.isLoggedIn()) {
        console.log('页面需要认证但用户未登录');
        alert('请先登录');
        window.location.href = '/api/v1/auth/login';
        return;
    }
    
    // 登录状态检查和UI更新
    if (authManager.isLoggedIn()) {
        console.log('用户已登录，验证token...');
        const isValid = await authManager.verifyToken();
        if (isValid) {
            updateUIForLoggedInUser();
        } else {
            updateUIForLoggedOutUser();
        }
    } else {
        console.log('用户未登录');
        updateUIForLoggedOutUser();
    }

    // 绑定表单事件
    bindAuthForms();

    // 初始化聊天框（如果存在）
    const chatboxContainer = document.getElementById('chatboxContainer');
    if (chatboxContainer) {
        console.log('🚀 初始化聊天框...');
        
        // 初始化聊天框（如果存在）
        setTimeout(async () => {
            const isOnline = await checkRAGServerStatus();
            if (isOnline) {
                // 只显示一次欢迎消息，不重复
                const existingMessages = document.querySelectorAll('.chatbox-message');
                if (existingMessages.length === 0) {
                    addMessage('👋 Hi! I\'m your investment assistant. I can help you analyze company information, stock data, and more. How can I assist you today?', 'bot');
                }
            } else {
                addMessage('⚠️ AI server is currently offline. Please ensure the RAG server is running and refresh the page to retry.', 'bot');
            }
        }, 1000);
    }

    // 聊天框外部点击关闭事件
    document.addEventListener('click', function(event) {
        const chatbox = document.getElementById('chatboxContainer');
        const toggle = document.getElementById('chatToggle');
        
        if (chatbox && toggle && chatboxOpen && 
            !chatbox.contains(event.target) && 
            !toggle.contains(event.target)) {
            toggleChatbox();
        }
    });

    // 防止点击聊天框内部时关闭
    if (chatboxContainer) {
        chatboxContainer.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }
});