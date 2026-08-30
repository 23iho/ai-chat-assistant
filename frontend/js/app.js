// API 配置
const API_BASE_URL = 'http://127.0.0.1:8000';

// 全局状态
let authToken = localStorage.getItem('auth_token') || null;
let currentUser = JSON.parse(localStorage.getItem('current_user') || 'null');
let conversations = [];  // [{id, title, updated_at, ...}]
let currentConversationId = null;  // 当前激活的会话 ID

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
    // 先拉会话列表，再加载当前会话的历史
    loadConversationList().then(() => {
        if (!currentConversationId) {
            // 没有激活会话：选列表里最近的一个，否则新建
            if (conversations.length > 0) {
                switchConversation(conversations[0].id);
            } else {
                createNewConversation();
            }
        } else {
            // 校验当前会话是否还存在
            const exists = conversations.some(c => c.id === currentConversationId);
            if (exists) {
                switchConversation(currentConversationId);
            } else if (conversations.length > 0) {
                switchConversation(conversations[0].id);
            } else {
                createNewConversation();
            }
        }
    });
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
        conversations = [];
        currentConversationId = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('current_user');
        localStorage.removeItem('current_conv_id');
        showAuthPage();

        // 清空输入框
        const loginUsername = document.getElementById('loginUsername');
        const loginPassword = document.getElementById('loginPassword');
        if (loginUsername) loginUsername.value = '';
        if (loginPassword) loginPassword.value = '';
    }
}

// ==================== 聊天相关函数 ====================// 流式生成状态：保存当前请求的 AbortController，让 stop 按钮能中止
let currentStreamController = null;


// ===== Markdown 渲染 =====
// 把纯文本渲染成 HTML（用于 AI 回复气泡）。
// 用 DOMPurify 防 XSS，用 highlight.js 高亮代码块。
// 流式渲染期间不调这个（会闪烁），等流结束再调。
function renderMarkdown(text) {
    if (!window.marked) {
        // 降级：纯文本转义
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    const rawHtml = marked.parse(text, { breaks: true, gfm: true });
    const cleanHtml = window.DOMPurify
        ? DOMPurify.sanitize(rawHtml, { ADD_ATTR: ['target'] })
        : rawHtml;
    return cleanHtml;
}

function highlightCodeBlocks(container) {
    if (!window.hljs) return;
    container.querySelectorAll('pre code').forEach(block => {
        try {
            hljs.highlightElement(block);
        } catch (e) {
            console.warn('代码高亮失败:', e);
        }
    });
}

// 把一个 assistant 消息 div 从纯文本切换到 Markdown 渲染
function rerenderAssistantMessageAsMarkdown(messageDiv) {
    if (!messageDiv) return;
    const text = messageDiv.textContent;  // 拿到当前累积的纯文本
    messageDiv.innerHTML = renderMarkdown(text);
    highlightCodeBlocks(messageDiv);
    const box = document.getElementById('chatMessages');
    if (box) box.scrollTop = box.scrollHeight;
}

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
            // conversation_id 为空时，后端会自动新建一个并通过 init 事件回传
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId,
                clear_history: false,
            }),
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

                if (payload.type === 'init') {
                    // 后端告诉我们这条消息属于哪个会话（可能是新建的）
                    if (payload.conversation_id !== currentConversationId) {
                        currentConversationId = payload.conversation_id;
                        localStorage.setItem('current_conv_id', String(currentConversationId));
                        const titleEl = document.getElementById('currentConvTitle');
                        if (titleEl) titleEl.textContent = payload.conversation_title || '';
                        // 把新会话插到列表顶部
                        const exists = conversations.some(c => c.id === currentConversationId);
                        if (!exists) {
                            conversations.unshift({
                                id: payload.conversation_id,
                                title: payload.conversation_title || '新对话',
                                updated_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
                            });
                            renderConversationList();
                        }
                    }
                } else if (payload.type === 'content') {
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
                    // 流结束；后端已经把完整内容存 DB
                    aiMsgDiv.classList.remove('streaming');
                    // 把累积的纯文本换成 Markdown 渲染
                    rerenderAssistantMessageAsMarkdown(aiMsgDiv);
                    // 刷新会话列表，让 updated_at 排到最前
                    loadConversationList();
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
    if (!chatMessages) return null;

    // 如果是第一条消息，移除欢迎消息
    if (chatMessages.querySelector('.welcome-message')) {
        chatMessages.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // user / error 用纯文本（安全、所见即所得）
    // assistant 走 Markdown 渲染（标题、列表、表格、代码块都好看）
    if (role === 'assistant' && window.marked) {
        messageDiv.innerHTML = renderMarkdown(content || '');
        highlightCodeBlocks(messageDiv);
    } else {
        messageDiv.textContent = content;
    }

    chatMessages.appendChild(messageDiv);

    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
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

// 加载历史记录列表（历史侧边栏，老接口保留兼容）
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

            const reversedHistory = [...data.data.history].reverse();

            reversedHistory.forEach(record => {
                const item = document.createElement('div');
                item.className = 'history-item';

                const roleEl = document.createElement('div');
                roleEl.className = 'role';
                roleEl.textContent = record.role === 'user' ? '👤 我' : '🤖 AI';

                const contentEl = document.createElement('div');
                contentEl.className = 'content';
                contentEl.textContent = record.content;
                contentEl.title = record.content;

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


// ==================== 会话（Conversation）管理 ====================

// 从 localStorage 恢复上次激活的会话
function restoreCurrentConversationId() {
    const saved = localStorage.getItem('current_conv_id');
    if (saved) currentConversationId = parseInt(saved, 10) || null;
}


// 加载并渲染会话列表
async function loadConversationList() {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations?limit=100`, {
            headers: { 'Authorization': `Bearer ${authToken}` },
        });
        const data = await response.json();
        if (data.code === 200) {
            conversations = data.data.conversations || [];
            renderConversationList();
        }
    } catch (error) {
        console.error('加载会话列表错误:', error);
    }
}


// 把会话列表画到侧边栏
function renderConversationList() {
    const listEl = document.getElementById('convList');
    if (!listEl) return;
    listEl.innerHTML = '';

    if (conversations.length === 0) {
        const empty = document.createElement('div');
        empty.style.cssText = 'padding:20px;text-align:center;color:#999;font-size:13px;';
        empty.textContent = '还没有会话，点上方按钮开聊吧~';
        listEl.appendChild(empty);
        return;
    }

    conversations.forEach(c => {
        const item = document.createElement('div');
        item.className = 'conv-item' + (c.id === currentConversationId ? ' active' : '');
        item.dataset.id = c.id;

        const titleEl = document.createElement('span');
        titleEl.className = 'conv-title';
        titleEl.textContent = c.title || '新对话';
        titleEl.title = c.title;

        const delBtn = document.createElement('button');
        delBtn.className = 'conv-del';
        delBtn.textContent = '×';
        delBtn.title = '删除会话';
        delBtn.onclick = (e) => {
            e.stopPropagation();  // 阻止冒泡触发切换
            deleteConversation(c.id);
        };

        item.onclick = () => switchConversation(c.id);

        item.appendChild(titleEl);
        item.appendChild(delBtn);
        listEl.appendChild(item);
    });
}


// 切换到指定会话
async function switchConversation(convId) {
    if (convId === currentConversationId) return;
    currentConversationId = convId;
    localStorage.setItem('current_conv_id', String(convId));

    const titleEl = document.getElementById('currentConvTitle');
    const conv = conversations.find(c => c.id === convId);
    if (titleEl) titleEl.textContent = conv ? conv.title : '';

    renderConversationList();  // 更新高亮
    await loadMessagesOfConversation(convId);
}


// 加载某个会话的所有消息到聊天框
async function loadMessagesOfConversation(convId) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    chatMessages.innerHTML = '';

    try {
        const response = await fetch(
            `${API_BASE_URL}/history?skip=0&limit=200&conversation_id=${convId}`,
            { headers: { 'Authorization': `Bearer ${authToken}` } }
        );
        const data = await response.json();

        if (data.code === 200) {
            if (data.data.history.length === 0) {
                addWelcomeMessage();
            } else {
                data.data.history.forEach(r => addMessageToChat(r.role, r.content));
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
    } catch (error) {
        console.error('加载会话历史错误:', error);
        addWelcomeMessage();
    }
}


// 新建会话
async function createNewConversation() {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify({}),
        });
        const data = await response.json();
        if (data.code === 200) {
            const conv = {
                id: data.data.id,
                title: data.data.title,
                updated_at: data.data.created_at,
            };
            conversations.unshift(conv);
            await switchConversation(conv.id);
        }
    } catch (error) {
        console.error('新建会话错误:', error);
        showError('新建会话失败，请重试');
    }
}


// 删除会话
async function deleteConversation(convId) {
    const conv = conversations.find(c => c.id === convId);
    if (!conv) return;
    if (!confirm(`确定删除会话「${conv.title}」？消息会一起被删掉。`)) return;

    try {
        const response = await fetch(`${API_BASE_URL}/conversations/${convId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` },
        });
        const data = await response.json();
        if (data.code === 200) {
            // 从本地列表里移除
            conversations = conversations.filter(c => c.id !== convId);
            // 如果删的就是当前会话，切到列表里下一个或新建
            if (convId === currentConversationId) {
                if (conversations.length > 0) {
                    await switchConversation(conversations[0].id);
                } else {
                    await createNewConversation();
                }
            } else {
                renderConversationList();
            }
        } else {
            showError(data.message || '删除失败');
        }
    } catch (error) {
        console.error('删除会话错误:', error);
        showError('网络错误，请重试');
    }
}


// 清空当前会话（消息全删，会话保留）
async function clearCurrentConversation() {
    if (!currentConversationId) return;
    if (!confirm('确定清空当前会话的所有消息？')) return;
    try {
        const response = await fetch(
            `${API_BASE_URL}/history?conversation_id=${currentConversationId}`,
            {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${authToken}` },
            }
        );
        const data = await response.json();
        if (data.code === 200) {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) chatMessages.innerHTML = '';
            addWelcomeMessage();
        } else {
            showError(data.message || '清空失败');
        }
    } catch (error) {
        console.error('清空会话错误:', error);
        showError('网络错误，请重试');
    }
}


// 移动端侧边栏抽屉
function toggleSidebar() {
    const sb = document.getElementById('convSidebar');
    if (sb) sb.classList.toggle('open');
}


// 页面初始化时尝试恢复当前会话 ID
restoreCurrentConversationId();


// 兼容旧函数名（避免之前清空按钮的 onclick 引用报错）
async function clearHistory() {
    return clearCurrentConversation();
}
async function loadChatHistory() {
    if (currentConversationId) {
        await loadMessagesOfConversation(currentConversationId);
    } else {
        addWelcomeMessage();
    }
}