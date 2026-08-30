// API 配置
const API_BASE_URL = 'http://127.0.0.1:8000';

// 全局状态
let authToken = localStorage.getItem('auth_token') || null;
let currentUser = JSON.parse(localStorage.getItem('current_user') || 'null');

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否已登录
    if (authToken && currentUser) {
        showChatPage();
    } else {
        showAuthPage();
    }

    // 绑定回车键发送消息
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // 自动调整输入框高度
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });
    }
});

// ==================== 认证相关函数 ====================

// 显示登录表单
function showLogin() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    if (loginForm) loginForm.style.display = 'block';
    if (registerForm) registerForm.style.display = 'none';
    hideError();
}

// 显示注册表单
function showRegister() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    if (loginForm) loginForm.style.display = 'none';
    if (registerForm) registerForm.style.display = 'block';
    hideError();
}

// 显示认证页面
function showAuthPage() {
    const authPage = document.getElementById('authPage');
    const chatPage = document.getElementById('chatPage');
    if (authPage) authPage.style.display = 'block';
    if (chatPage) chatPage.classList.remove('active');
}

// 显示聊天页面
function showChatPage() {
    const authPage = document.getElementById('authPage');
    const chatPage = document.getElementById('chatPage');
    const currentUsername = document.getElementById('currentUsername');
    
    if (authPage) authPage.style.display = 'none';
    if (chatPage) chatPage.classList.add('active');
    if (currentUsername && currentUser) {
        currentUsername.textContent = `欢迎，${currentUser.username}`;
    }
    loadChatHistory();
}

// 显示错误信息
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.add('show');
        
        // 3秒后自动隐藏
        setTimeout(() => {
            hideError();
        }, 3000);
    } else {
        // 如果没有错误提示元素，回退到 alert
        alert(message);
    }
}

// 隐藏错误信息
function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.classList.remove('show');
    }
}

// 处理登录
async function handleLogin() {
    const usernameEl = document.getElementById('loginUsername');
    const passwordEl = document.getElementById('loginPassword');
    
    if (!usernameEl || !passwordEl) return;

    const username = usernameEl.value.trim();
    const password = passwordEl.value;

    if (!username || !password) {
        showError('请输入用户名和密码');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.code === 200) {
            authToken = data.data.access_token;
            currentUser = { username };
            
            // 保存到本地存储
            localStorage.setItem('auth_token', authToken);
            localStorage.setItem('current_user', JSON.stringify(currentUser));
            
            showChatPage();
        } else {
            showError(data.message || '登录失败');
        }
    } catch (error) {
        console.error('登录错误:', error);
        showError('网络错误，请检查后端服务是否启动');
    }
}

// 处理注册
async function handleRegister() {
    const usernameEl = document.getElementById('regUsername');
    const emailEl = document.getElementById('regEmail');
    const passwordEl = document.getElementById('regPassword');

    if (!usernameEl || !passwordEl) return;

    const username = usernameEl.value.trim();
    const email = emailEl ? emailEl.value.trim() : '';
    const password = passwordEl.value;

    if (!username || !password) {
        showError('请填写必填字段');
        return;
    }

    if (username.length < 3 || username.length > 20) {
        showError('用户名长度必须在3-20个字符之间');
        return;
    }

    if (password.length < 6) {
        showError('密码长度至少为6个字符');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (data.code === 200) {
            showError('✓ 注册成功！请登录');
            setTimeout(() => {
                showLogin();
                // 清空注册表单
                if (usernameEl) usernameEl.value = '';
                if (emailEl) emailEl.value = '';
                if (passwordEl) passwordEl.value = '';
            }, 1500);
        } else {
            showError(data.message || '注册失败');
        }
    } catch (error) {
        console.error('注册错误:', error);
        showError('网络错误，请检查后端服务是否启动');
    }
}

// 处理退出登录
function handleLogout() {
    if (confirm('确定要退出登录吗？')) {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('current_user');
        showAuthPage();
        
        // 清空输入框
        const loginUsername = document.getElementById('loginUsername');
        const loginPassword = document.getElementById('loginPassword');
        if (loginUsername) loginUsername.value = '';
        if (loginPassword) loginPassword.value = '';
    }
}

// ==================== 聊天相关函数 ====================

// 流式生成状态：保存当前请求的 AbortController，让 stop 按钮能中止
let currentStreamController = null;

// 停止当前生成
function stopGeneration() {
    if (currentStreamController) {
        currentStreamController.abort();
        currentStreamController = null;
    }
    setStreamingUI(false);
}

// 切换 UI：发送中时禁用输入，显示停止按钮
function setStreamingUI(isStreaming) {
    const btnSend = document.getElementById('btnSend');
    const btnStop = document.getElementById('btnStop');
    const input = document.getElementById('messageInput');
    if (btnSend) btnSend.style.display = isStreaming ? 'none' : '';
    if (btnStop) btnStop.style.display = isStreaming ? '' : 'none';
    if (input) input.disabled = isStreaming;
}

// 解析 SSE 一段 buffer，返回 [{event, data}, ...] 与剩余 buffer
function parseSSEChunk(buffer) {
    const events = [];
    let idx;
    // 用 \n\n 切分事件块
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const raw = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const lines = raw.split('\n');
        const dataLines = lines
            .filter(l => l.startsWith('data:'))
            .map(l => l.slice(5).trim());
        if (dataLines.length === 0) continue;
        events.push(dataLines.join('\n'));
    }
    return { events, rest: buffer };
}

// 发送消息（流式）
async function sendMessage() {
    const input = document.getElementById('messageInput');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    // 清空输入框并重置高度
    input.value = '';
    input.style.height = 'auto';

    addMessageToChat('user', message);

    // 创建 AI 回复占位（带 streaming class 显示光标动画）
    const aiMsgDiv = addMessageToChat('assistant', '');
    aiMsgDiv.classList.add('streaming');

    // 切换 UI 状态
    setStreamingUI(true);
    currentStreamController = new AbortController();

    let fullContent = '';
    let buffer = '';

    try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify({ message: message, clear_history: false }),
            signal: currentStreamController.signal,
        });

        // 401 直接跳登录（之前 token 过期是静默失败）
        if (response.status === 401) {
            showError('登录已过期，请重新登录');
            handleLogout();
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const { events, rest } = parseSSEChunk(buffer);
            buffer = rest;

            for (const evt of events) {
                if (evt === '[DONE]') continue;
                let payload;
                try {
                    payload = JSON.parse(evt);
                } catch (e) {
                    console.warn('SSE JSON 解析失败:', evt);
                    continue;
                }

                if (payload.type === 'content') {
                    fullContent += payload.text;
                    aiMsgDiv.textContent = fullContent;
                    // 自动滚到底
                    const box = document.getElementById('chatMessages');
                    if (box) box.scrollTop = box.scrollHeight;
                } else if (payload.type === 'error') {
                    aiMsgDiv.classList.remove('streaming');
                    aiMsgDiv.classList.add('error');
                    aiMsgDiv.textContent = `错误: ${payload.message}`;
                } else if (payload.type === 'info') {
                    aiMsgDiv.textContent = payload.message;
                } else if (payload.type === 'done') {
                    // 流结束；后端已经把完整内容存 DB，这里只需去掉 streaming class
                    aiMsgDiv.classList.remove('streaming');
                }
            }
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            aiMsgDiv.classList.remove('streaming');
            aiMsgDiv.textContent = (fullContent || '') + (fullContent ? '\n\n[已停止生成]' : '[已停止生成]');
        } else {
            console.error('发送消息错误:', error);
            aiMsgDiv.classList.remove('streaming');
            aiMsgDiv.classList.add('error');
            aiMsgDiv.textContent = `网络错误：${error.message || error}`;
        }
    } finally {
        currentStreamController = null;
        setStreamingUI(false);
    }
}

// 添加消息到聊天界面
function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // 如果是第一条消息，移除欢迎消息
    if (chatMessages.querySelector('.welcome-message')) {
        chatMessages.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = content;
    
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 清空聊天历史
async function clearHistory() {
    if (!confirm('确定要清空所有聊天记录吗？此操作不可恢复。')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/history`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (data.code === 200) {
            // 清空聊天界面
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.innerHTML = `
                    <div class="welcome-message">
                        <p>✓ 聊天记录已清空，开始新的对话吧~</p>
                    </div>
                `;
            }
        } else {
            alert(data.message || '清空失败');
        }
    } catch (error) {
        console.error('清空历史记录错误:', error);
        alert('网络错误，请稍后重试');
    }
}

// 加载聊天历史
async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history?skip=0&limit=50`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        // 先清空当前聊天框，防止切换用户后残留旧数据
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }

        if (data.code === 200 && data.data.history.length > 0) {
            // 显示历史消息
            data.data.history.forEach(record => {
                addMessageToChat(record.role, record.content);
            });
        } else {
            // 无历史记录时显示欢迎信息
            addWelcomeMessage();
        }
    } catch (error) {
        console.error('加载历史记录错误:', error);
    }
}

// 显示欢迎信息
function addWelcomeMessage() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome-message';
    welcomeDiv.innerHTML = '<p>你好！我是AI聊天助手，有什么可以帮助你的吗？</p>';
    chatMessages.appendChild(welcomeDiv);
}

// ==================== 侧边栏相关函数 ====================

// 切换历史记录侧边栏
async function toggleHistory() {
    const sidebar = document.getElementById('historySidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
        
        if (sidebar.classList.contains('active')) {
            await loadHistoryList();
        }
    }
}

// 加载历史记录列表
async function loadHistoryList() {
    try {
        const response = await fetch(`${API_BASE_URL}/history?skip=0&limit=100`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (data.code === 200) {
            const historyList = document.getElementById('historyList');
            if (!historyList) return;

            historyList.innerHTML = '';
            
            if (data.data.history.length === 0) {
                historyList.innerHTML = '<p style="text-align: center; color: #999; padding: 20px;">暂无聊天记录</p>';
                return;
            }
            
            // 按时间倒序显示
            const reversedHistory = [...data.data.history].reverse();
            
            reversedHistory.forEach(record => {
                const item = document.createElement('div');
                item.className = 'history-item';

                // 之前用 innerHTML 拼 record.content 是存储型 XSS：
                // 用户发一条 <img src=x onerror=alert(1)> 就会被持久化，
                // 下次任何人打开侧边栏都会触发（主聊天区用 textContent 是安全的）。
                // 改成 createElement + textContent，浏览器自动转义。
                const roleEl = document.createElement('div');
                roleEl.className = 'role';
                roleEl.textContent = record.role === 'user' ? '👤 我' : '🤖 AI';

                const contentEl = document.createElement('div');
                contentEl.className = 'content';
                contentEl.textContent = record.content;
                contentEl.title = record.content;  // 鼠标悬停看完整内容

                const timeEl = document.createElement('div');
                timeEl.className = 'time';
                timeEl.textContent = record.create_time;

                item.appendChild(roleEl);
                item.appendChild(contentEl);
                item.appendChild(timeEl);
                historyList.appendChild(item);
            });
        }
    } catch (error) {
        console.error('加载历史列表错误:', error);
    }
}