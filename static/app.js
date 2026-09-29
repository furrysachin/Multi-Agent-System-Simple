const form = document.querySelector('#chatForm');
const input = document.querySelector('#messageInput');
const sendButton = document.querySelector('#sendButton');
const messageList = document.querySelector('#messageList');
const welcome = document.querySelector('#welcome');
const chatList = document.querySelector('#chatList');
const sidebar = document.querySelector('#sidebar');
const backdrop = document.querySelector('#mobileBackdrop');

let chats = [createChat()];
let activeChat = chats[0];

function createChat() {
  return { id: crypto.randomUUID(), title: 'New trip', messages: [] };
}

function iconMarkup() {
  return '<span class="assistant-avatar" aria-hidden="true"><span></span></span>';
}

function renderChatList() {
  chatList.replaceChildren();
  chats.forEach((chat) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `history-item${chat === activeChat ? ' active' : ''}`;
    button.textContent = chat.title;
    button.title = chat.title;
    button.addEventListener('click', () => selectChat(chat));
    chatList.append(button);
  });
}

function addMessage(role, text, loading = false) {
  const row = document.createElement('div');
  row.className = `message ${role}${loading ? ' loading' : ''}`;
  if (role === 'assistant') row.innerHTML = iconMarkup();
  const content = document.createElement('div');
  content.className = 'message-content';
  if (loading) {
    content.setAttribute('aria-label', 'Assistant is thinking');
    content.innerHTML = '<span class="loading-dot"></span><span class="loading-dot"></span><span class="loading-dot"></span>';
  } else {
    content.textContent = text;
  }
  row.append(content);
  messageList.append(row);
  messageList.scrollTo({ top: messageList.scrollHeight, behavior: 'smooth' });
  return { row, content };
}

function renderMessages() {
  messageList.replaceChildren();
  welcome.hidden = activeChat.messages.length > 0;
  activeChat.messages.forEach(({ role, text }) => addMessage(role, text));
  renderChatList();
}

function selectChat(chat) {
  activeChat = chat;
  renderMessages();
  closeSidebar();
  input.focus();
}

function startNewChat() {
  const chat = createChat();
  chats.unshift(chat);
  selectChat(chat);
}

function closeSidebar() {
  sidebar.classList.remove('open');
  backdrop.classList.remove('visible');
}

async function sendMessage(message) {
  const text = message.trim();
  if (!text || sendButton.disabled) return;

  const chat = activeChat;
  welcome.hidden = true;
  chat.messages.push({ role: 'user', text });
  if (chat.messages.length === 1) {
    chat.title = text.split(/\s+/).slice(0, 5).join(' ');
  }
  addMessage('user', text);
  renderChatList();
  input.value = '';
  input.style.height = 'auto';
  sendButton.disabled = true;
  const loading = addMessage('assistant', '', true);

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, thread_id: activeChat.id }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Something went wrong. Please try again.');
    loading.row.remove();
    chat.messages.push({ role: 'assistant', text: data.answer });
    if (activeChat === chat) addMessage('assistant', data.answer);
  } catch (error) {
    loading.row.remove();
    const errorText = error.message || 'Could not reach the assistant. Please try again.';
    chat.messages.push({ role: 'assistant', text: errorText });
    if (activeChat === chat) addMessage('assistant', errorText);
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
});

input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelector('#newChat').addEventListener('click', startNewChat);
document.querySelector('#openSidebar').addEventListener('click', () => {
  sidebar.classList.add('open');
  backdrop.classList.add('visible');
});
document.querySelector('#closeSidebar').addEventListener('click', closeSidebar);
backdrop.addEventListener('click', closeSidebar);
document.querySelectorAll('.suggestion').forEach((button) => {
  button.addEventListener('click', () => sendMessage(button.dataset.prompt));
});

document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    startNewChat();
  }
  if (event.key === 'Escape') closeSidebar();
});

renderChatList();
