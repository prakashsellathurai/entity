const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

let history = [];

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Handle Enter key
userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';

    // Remove welcome message if present
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Add user message
    addMessage(text, 'user');

    // Check if it's a command
    if (text.toLowerCase().startsWith('run:')) {
        const command = text.substring(4).trim();
        await executeCommand(command);
    } else {
        await sendChat(text);
    }
}

function addMessage(content, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (role === 'assistant') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    div.appendChild(contentDiv);
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendChat(message) {
    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.innerHTML = '<div class="message-content">Typing...</div>';
    chatContainer.appendChild(loadingDiv);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, history })
        });
        
        const data = await response.json();
        loadingDiv.remove();
        
        if (data.response) {
            addMessage(data.response, 'assistant');
            history.push({ role: 'user', content: message });
            history.push({ role: 'assistant', content: data.response });
        }
    } catch (error) {
        loadingDiv.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    }
}

async function executeCommand(command) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.innerHTML = '<div class="message-content">Executing...</div>';
    chatContainer.appendChild(loadingDiv);

    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        
        const data = await response.json();
        loadingDiv.remove();
        
        let output = '';
        if (data.stdout) output += data.stdout;
        if (data.stderr) output += `\nError:\n${data.stderr}`;
        if (!output) output = 'Command executed successfully (no output).';

        addMessage(`\`\`\`bash\n${output}\n\`\`\``, 'assistant');
        
    } catch (error) {
        loadingDiv.remove();
        addMessage(`Error: ${error.message}`, 'assistant');
    }
}
