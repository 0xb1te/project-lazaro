// DOM Elements
const dropArea = document.getElementById("drop-area");
const chatHistory = document.getElementById("chat-history");
const chatInput = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");
const debugButton = document.getElementById("debug-button");

// State
let isProcessing = false;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  addMessage("bot", "Hello! How can I assist you today?");
  setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropArea.addEventListener(
      eventName,
      () => dropArea.classList.add("highlight"),
      false
    );
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(
      eventName,
      () => dropArea.classList.remove("highlight"),
      false
    );
  });

  dropArea.addEventListener("drop", handleDrop, false);

  chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    const newHeight = Math.min(chatInput.scrollHeight, 300);
    chatInput.style.height = `${newHeight}px`;
  });

  sendButton.addEventListener("click", handleSendMessage);
  debugButton.addEventListener("click", handleDebugClick);
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function handleDrop(e) {
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    uploadFile(files[0]);
  }
}

async function uploadFile(file) {
  if (isProcessing) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    isProcessing = true;
    toggleLoadingState(true);

    const response = await fetch(`/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to upload file");
    }

    const data = await response.json();
    addMessage("bot", data.message);
  } catch (error) {
    addMessage("bot", `Error: ${error.message}`);
  } finally {
    isProcessing = false;
    toggleLoadingState(false);
  }
}

async function handleSendMessage() {
  if (isProcessing) return;

  const question = chatInput.value.trim();
  if (!question) return;

  try {
    isProcessing = true;
    toggleLoadingState(true);

    // Add user message
    addMessage("user", question);
    chatInput.value = "";
    chatInput.style.height = "auto";

    // Add temporary loading message
    const loadingMessageElement = addMessage("bot", "", true);

    const response = await fetch(`/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Remove loading message and add response
    if (loadingMessageElement) {
      loadingMessageElement.remove();
    }
    addMessage("bot", formatMessage(data.answer));

  } catch (error) {
    console.error('Error:', error);
    if (loadingMessageElement) {
      loadingMessageElement.remove();
    }
    addMessage("bot", `Error: ${error.message}`);
  } finally {
    isProcessing = false;
    toggleLoadingState(false);
  }
}

async function handleDebugClick() {
  if (isProcessing) return;

  try {
    isProcessing = true;
    toggleLoadingState(true);

    const response = await fetch(`/debug/collection`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const formattedDebug = `Debug Collection:\n${JSON.stringify(data, null, 2)}`;
    addMessage("bot", formattedDebug);
  } catch (error) {
    addMessage("bot", `Error: ${error.message}`);
  } finally {
    isProcessing = false;
    toggleLoadingState(false);
  }
}

function addMessage(role, message, isLoading = false) {
  const messageElement = document.createElement("div");
  messageElement.classList.add("message", `${role}-message`);

  if (isLoading) {
    messageElement.innerHTML = `
      <div class="typing-indicator">
        <span></span><span></span><span></span>
      </div>
    `;
  } else {
    messageElement.innerHTML = role === "bot" ? formatMessage(message) : message;

    messageElement.querySelectorAll("pre code").forEach((block) => {
      hljs.highlightElement(block);
    });
  }

  chatHistory.appendChild(messageElement);
  chatHistory.scrollTop = chatHistory.scrollHeight;
  return messageElement;
}

function formatMessage(message) {
  if (!message) return "";

  message = message.trim();

  try {
    const parsedMessage = JSON.parse(message);
    message = parsedMessage.answer || parsedMessage.message || message;
  } catch (e) {
    // Not JSON, continue
  }

  // Process headers
  message = message.replace(/^(#{1,6})\s(.+)$/gm, (match, hashes, content) => {
    const level = hashes.length;
    return `<h${level} class="markdown-header header-${level}">${content}</h${level}>`;
  });

  // Process bold text
  message = message.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Process code blocks with language
  message = message.replace(
    /```(\w+)?\n([\s\S]+?)```/g,
    (match, language = "", code) => {
      const uniqueId = `code-block-${Math.random().toString(36).substr(2, 9)}`;
      return `
        <div class="code-block" id="${uniqueId}">
          <div class="code-header">
            <div class="code-header-left">
              <span class="code-language">${language}</span>
            </div>
            <div class="code-header-right">
              <button class="copy-button" onclick="copyToClipboard('${uniqueId}')">
                <svg class="copy-icon" viewBox="0 0 24 24" width="16" height="16">
                  <path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                </svg>
                <span>Copy</span>
              </button>
            </div>
          </div>
          <pre><code class="${language ? `language-${language}` : ''}">${escapeHtml(code.trim())}</code></pre>
        </div>
      `;
    }
  );

  return message;
}

function copyToClipboard(blockId) {
  const codeBlock = document.getElementById(blockId);
  const codeContent = codeBlock.querySelector("code").textContent;

  navigator.clipboard.writeText(codeContent)
    .then(() => {
      const button = codeBlock.querySelector(".copy-button");
      const originalContent = button.innerHTML;
      button.innerHTML = `
        <svg class="copy-icon" viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
        </svg>
        <span>Copied!</span>
      `;
      button.classList.add("copied");

      setTimeout(() => {
        button.innerHTML = originalContent;
        button.classList.remove("copied");
      }, 2000);
    })
    .catch(() => showNotification("Failed to copy code", "error"));
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function toggleLoadingState(isLoading) {
  sendButton.disabled = isLoading;
  debugButton.disabled = isLoading;
  dropArea.style.opacity = isLoading ? "0.5" : "1";
}

function showNotification(message, type = "success") {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => notification.remove(), 3000);
}