// Constants
const API_BASE_URL = "http://127.0.0.1:5000";

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
  // Drag and drop events
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });

  // Highlight drop area
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

  // File drop handling
  dropArea.addEventListener("drop", handleDrop, false);

  // Chat input handling
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

// File Handling
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

// API Interactions
async function uploadFile(file) {
  if (isProcessing) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    isProcessing = true;
    toggleLoadingState(true);
    console.log("Updating");
    const response = await fetch(`${API_BASE_URL}/upload`, {
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

    addMessage("user", question);
    chatInput.value = "";
    chatInput.style.height = "auto";

    // Add loading message
    const loadingMessage = addMessage("bot", "", true);

    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();
    loadingMessage.remove();
    addMessage("bot", formatMessage(data.answer));
  } catch (error) {
    loadingMessage?.remove();
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

    const response = await fetch(`${API_BASE_URL}/debug/collection`);
    const data = await response.json();
    const formattedDebug = `Debug Collection:\n${JSON.stringify(
      data,
      null,
      2
    )}`;
    addMessage("bot", formattedDebug);
  } catch (error) {
    addMessage("bot", `Error: ${error.message}`);
  } finally {
    isProcessing = false;
    toggleLoadingState(false);
  }
}

// Message Handling
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
    // Process message if it's from bot and contains special formatting
    messageElement.innerHTML =
      role === "bot" ? formatMessage(message) : message;

    // Initialize syntax highlighting for code blocks
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

  // Try to parse JSON
  try {
    const parsedMessage = JSON.parse(message);
    message = parsedMessage.answer || parsedMessage.message || message;
  } catch (e) {
    // Not JSON, continue
  }

  // Process headers (before other formatting)
  message = message.replace(/^(#{1,6})\s(.+)$/gm, (match, hashes, content) => {
    const level = hashes.length;
    return `<h${level} class="markdown-header header-${level}">${content}</h${level}>`;
  });

  // Process bold text
  message = message.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Process thought blocks
  message = message.replace(/<think>([\s\S]*?)<\/think>/g, (match, content) => {
    const cleanContent = content
      .split("\n")
      .filter((line) => line.trim())
      .join("<br>");

    return `
      <div class="thought-block">
        <div class="thought-header">
          <svg class="thought-icon" viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10s10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8s8 3.59 8 8s-3.59 8-8 8zm-1-4h2v2h-2zm1.61-9.96c-2.06-.3-3.88.97-4.43 2.79-.18.58.26 1.17.87 1.17h.2c.41 0 .74-.29.88-.67.32-.89 1.27-1.5 2.3-1.28.95.2 1.65 1.13 1.57 2.1-.1 1.34-1.62 1.63-2.45 2.88 0 .01-.01.01-.01.02-.01.02-.02.03-.03.05-.09.15-.18.32-.25.5-.01.03-.03.05-.04.08-.01.02-.01.04-.02.07-.12.34-.2.75-.2 1.25h2c0-.42.11-.77.28-1.07.02-.03.03-.06.05-.09.08-.14.18-.27.28-.39.01-.01.02-.03.03-.04.1-.12.21-.23.33-.34.96-.91 2.26-1.65 1.99-3.56-.24-1.74-1.61-3.21-3.35-3.47z"/>
          </svg>
          <span>Análisis del Pensamiento</span>
        </div>
        <div class="thought-content">${cleanContent}</div>
      </div>
    `;
  });

  // Process code blocks (rest of the function remains the same)
  message = message.replace(
    /```(\w+)([\s\S]+?)```/g,
    (match, language, code) => {
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
        <pre><code class="language-${language}">${escapeHtml(
        code.trim()
      )}</code></pre>
      </div>
    `;
    }
  );

  return message;
}

function copyToClipboard(blockId) {
  const codeBlock = document.getElementById(blockId);
  const codeContent = codeBlock.querySelector("code").textContent;

  navigator.clipboard
    .writeText(codeContent)
    .then(() => {
      // Update button text temporarily
      const button = codeBlock.querySelector(".copy-button");
      const originalContent = button.innerHTML;
      button.innerHTML = `
        <svg class="copy-icon" viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
        </svg>
        <span>Copied!</span>
      `;
      button.classList.add("copied");

      // Reset button after delay
      setTimeout(() => {
        button.innerHTML = originalContent;
        button.classList.remove("copied");
      }, 2000);
    })
    .catch(() => showNotification("Failed to copy code", "error"));
}

// Utility Functions
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function copyCode(element) {
  const code = element.querySelector("code").textContent;
  navigator.clipboard
    .writeText(code)
    .then(() => showNotification("Code copied to clipboard!"))
    .catch(() => showNotification("Failed to copy code", "error"));
}

function showNotification(message, type = "success") {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => notification.remove(), 3000);
}

function toggleLoadingState(isLoading) {
  sendButton.disabled = isLoading;
  debugButton.disabled = isLoading;
  dropArea.style.opacity = isLoading ? "0.5" : "1";
}
