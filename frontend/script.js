// Constants
const API_BASE_URL = ''; // Empty for relative URLs
const DEFAULT_MODEL = "llama2";

// DOM Elements
const sidebar = document.getElementById("sidebar");
const toggleSidebarBtn = document.getElementById("toggle-sidebar");
const chatHistory = document.getElementById("chat-history");
const chatInput = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");
const debugButton = document.getElementById("debug-button");
const newChatButton = document.getElementById("new-chat-btn");
const conversationsList = document.getElementById("conversations-list");
const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("file-input");
const dropOverlay = document.getElementById("drop-overlay");
const toast = document.getElementById("toast");
const modelName = document.getElementById("model-name");
const currentConversationTitle = document.getElementById("current-conversation-title");
const editTitleBtn = document.getElementById("edit-title-btn");
const editTitleModal = document.getElementById("edit-title-modal");
const editTitleInput = document.getElementById("edit-title-input");
const saveEditTitleBtn = document.getElementById("save-edit-title");
const cancelEditTitleBtn = document.getElementById("cancel-edit-title");
const conversationDocuments = document.getElementById("conversation-documents");

// Templates
const conversationTemplate = document.getElementById("conversation-template");
const messageTemplate = document.getElementById("message-template");

// State
let activeConversationId = null;
let isProcessing = false;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadConversations();
  updateModelInfo();
});

// Event Listeners
function setupEventListeners() {
  // Toggle sidebar
  toggleSidebarBtn.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
  });

  // Drag and drop events
  ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  document.body.addEventListener("dragenter", () => {
    dropOverlay.style.display = "flex";
  });

  dropOverlay.addEventListener("dragleave", e => {
    const rect = dropOverlay.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;

    if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
      dropOverlay.style.display = "none";
    }
  });

  dropOverlay.addEventListener("drop", e => {
    dropOverlay.style.display = "none";
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  });

  // Drop area in sidebar
  dropArea.addEventListener("drop", e => {
    preventDefaults(e);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  });

  // File input
  fileInput.addEventListener("change", e => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  // Chat input handling
  chatInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 128) + "px";
  });

  // Buttons
  sendButton.addEventListener("click", handleSendMessage);
  debugButton.addEventListener("click", handleDebugClick);
  newChatButton.addEventListener("click", createNewConversation);

  // Edit title functionality
  editTitleBtn.addEventListener("click", () => {
    if (activeConversationId) {
      editTitleInput.value = currentConversationTitle.textContent.trim();
      editTitleModal.style.display = "flex";
      editTitleInput.focus();
    }
  });

  saveEditTitleBtn.addEventListener("click", async () => {
    const newTitle = editTitleInput.value.trim();
    if (newTitle && activeConversationId) {
      await updateConversationTitle(activeConversationId, newTitle);
      editTitleModal.style.display = "none";
    }
  });

  cancelEditTitleBtn.addEventListener("click", () => {
    editTitleModal.style.display = "none";
  });

  // Close modal on outside click
  editTitleModal.addEventListener("click", (e) => {
    if (e.target === editTitleModal) {
      editTitleModal.style.display = "none";
    }
  });

  // Handle Enter key in title edit input
  editTitleInput.addEventListener("keydown", async (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const newTitle = editTitleInput.value.trim();
      if (newTitle && activeConversationId) {
        await updateConversationTitle(activeConversationId, newTitle);
        editTitleModal.style.display = "none";
      }
    } else if (e.key === "Escape") {
      editTitleModal.style.display = "none";
    }
  });
}

// File Handling
function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

async function uploadFile(file) {
  if (isProcessing) return;

  const formData = new FormData();
  formData.append("file", file);

  // Add conversation ID if one is active
  if (activeConversationId) {
    formData.append("conversation_id", activeConversationId);
  }

  try {
    isProcessing = true;
    toggleLoadingState(true);
    showToast("Uploading file...", "info");

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Error uploading file");
    }

    const data = await response.json();
    showToast(data.message, "success");

    // If a new conversation was created, set it as active
    if (data.conversation_id && data.conversation_id !== activeConversationId) {
      activeConversationId = data.conversation_id;
      await loadConversations();
      renderActiveConversation();
    } else {
      // Refresh the current conversation
      await loadConversation(activeConversationId);
    }
  } catch (error) {
    showToast(`Error: ${error.message}`, "error");
  } finally {
    isProcessing = false;
    toggleLoadingState(false);
  }
}

// Conversation Management
async function loadConversations() {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`);

    if (!response.ok) {
      throw new Error("Failed to load conversations");
    }

    const data = await response.json();

    // If there are conversations available
    if (data.conversations && data.conversations.length > 0) {
      // Set the first conversation as active if none is active
      if (!activeConversationId) {
        activeConversationId = data.conversations[0].id;
      }

      renderConversationsList(data.conversations);
      await loadConversation(activeConversationId);
    } else {
      // Create a new conversation if none exist
      await createNewConversation();
    }
  } catch (error) {
    console.error("Error loading conversations:", error);
    showToast(`Error loading conversations: ${error.message}`, "error");

    // Create a new conversation if we couldn't load any
    if (!activeConversationId) {
      await createNewConversation();
    }
  }
}

async function loadConversation(conversationId) {
  if (!conversationId) return;

  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`);

    if (!response.ok) {
      throw new Error("Failed to load conversation");
    }

    const conversation = await response.json();
    renderConversation(conversation);

    return conversation;
  } catch (error) {
    console.error(`Error loading conversation ${conversationId}:`, error);
    showToast(`Error loading conversation: ${error.message}`, "error");
  }
}

async function createNewConversation(title = "New Conversation") {
  try {
    // Ensure title is a string
    if (typeof title !== 'string') {
      console.error("Invalid title type:", typeof title);
      title = "New Conversation";
    }

    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: title,
        initial_message: "Hello! How can I help you with your code?"
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to create new conversation");
    }

    const conversation = await response.json();
    activeConversationId = conversation.id;

    // Reload conversations to update the list
    await loadConversations();

    // Render the new conversation
    renderConversation(conversation);

    // Clear input
    chatInput.value = "";
    chatInput.style.height = "auto";

    return conversation;
  } catch (error) {
    console.error("Error creating conversation:", error);
    showToast(`Error creating conversation: ${error.message}`, "error");
  }
}

async function deleteConversation(id) {
  // Prevent event propagation
  event.stopPropagation();

  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error("Failed to delete conversation");
    }

    // If we're deleting the active conversation, we need to set a new active one
    if (activeConversationId === id) {
      activeConversationId = null;
    }

    // Reload conversations
    await loadConversations();

    // If no conversation is active, create a new one
    if (!activeConversationId) {
      await createNewConversation();
    } else {
      await loadConversation(activeConversationId);
    }

    showToast("Conversation deleted successfully", "success");
  } catch (error) {
    console.error("Error deleting conversation:", error);
    showToast(`Error deleting conversation: ${error.message}`, "error");
  }
}

async function updateConversationTitle(id, newTitle) {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: newTitle
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to update conversation title");
    }

    // Reload conversations to update the list
    await loadConversations();

    // Update the title in the UI if it's the active conversation
    if (id === activeConversationId) {
      currentConversationTitle.textContent = newTitle;
    }

    showToast("Title updated successfully", "success");
  } catch (error) {
    console.error("Error updating conversation title:", error);
    showToast(`Error updating title: ${error.message}`, "error");
  }
}

async function setActiveConversation(id) {
  activeConversationId = id;
  await loadConversation(id);
}

// UI Rendering
function renderConversationsList(conversations) {
  conversationsList.innerHTML = "";

  conversations.forEach(conversation => {
    const conversationNode = conversationTemplate.content.cloneNode(true);
    const conversationItem = conversationNode.querySelector(".conversation-item");
    const titleElement = conversationNode.querySelector(".conversation-title");
    const deleteButton = conversationNode.querySelector(".delete-conversation");

    conversationItem.dataset.id = conversation.id;
    titleElement.textContent = conversation.title;

    // Mark active conversation
    if (conversation.id === activeConversationId) {
      conversationItem.classList.add("active");
    }

    // Add event listeners
    conversationItem.addEventListener("click", () => {
      setActiveConversation(conversation.id);
    });

    titleElement.addEventListener("dblclick", () => {
      // Create input element for editing
      const input = document.createElement("input");
      input.type = "text";
      input.value = conversation.title;
      input.className = "w-full p-1 border rounded";

      // Replace title with input
      titleElement.replaceWith(input);
      input.focus();

      // Handle input events
      input.addEventListener("blur", async () => {
        if (input.value.trim() !== conversation.title) {
          await updateConversationTitle(conversation.id, input.value.trim());
        } else {
          // Just replace the input with the original title
          input.replaceWith(titleElement);
        }
      });

      input.addEventListener("keydown", async (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          if (input.value.trim() !== conversation.title) {
            await updateConversationTitle(conversation.id, input.value.trim());
          } else {
            // Just replace the input with the original title
            input.replaceWith(titleElement);
          }
        } else if (e.key === "Escape") {
          // Cancel editing
          input.replaceWith(titleElement);
        }
      });
    });

    deleteButton.addEventListener("click", () => {
      deleteConversation(conversation.id);
    });

    conversationsList.appendChild(conversationNode);
  });
}

function renderConversation(conversation) {
  console.log("Rendering new conversation", conversation);
  // Set the title
  currentConversationTitle.textContent = conversation.title;

  // Clear chat history
  chatHistory.innerHTML = "";

  // Render each message
  if (conversation.messages && conversation.messages.length > 0) {
    conversation.messages.forEach(message => {
      renderMessage(message);
    });
  }

  // Render associated documents
  renderConversationDocuments(conversation.documents || []);

  // Scroll to bottom
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function renderConversationDocuments(documents) {
  // Clear current documents
  conversationDocuments.innerHTML = "";

  if (documents.length === 0) {
    conversationDocuments.style.display = "none";
    return;
  }

  conversationDocuments.style.display = "block";

  // Add a label if there are documents
  if (documents.length > 0) {
    const label = document.createElement("div");
    label.className = "text-xs text-slate-500 mb-1";
    label.textContent = "Documents:";
    conversationDocuments.appendChild(label);
  }

  // Add document items
  const docsContainer = document.createElement("div");
  docsContainer.className = "flex flex-wrap";

  documents.forEach(doc => {
    const template = document.getElementById("document-template");
    const docNode = template.content.cloneNode(true);
    const docItem = docNode.querySelector(".document-item");
    const docName = docNode.querySelector(".document-name");

    docName.textContent = doc.filename;

    // Set different icon for zip files
    if (doc.filename.endsWith(".zip")) {
      const docIcon = docItem.querySelector("svg");
      docIcon.innerHTML = `
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z M12 2v2m0 10v2m0-6v2" />
      `;
    }

    docsContainer.appendChild(docNode);
  });

  conversationDocuments.appendChild(docsContainer);
}

function renderActiveConversation() {
  if (activeConversationId) {
    loadConversation(activeConversationId);
  }
}

function renderMessage(message) {
  const messageNode = messageTemplate.content.cloneNode(true);
  const messageElement = messageNode.querySelector(".message");
  const avatarElement = messageNode.querySelector(".message-avatar");
  const bubbleElement = messageNode.querySelector(".message-bubble");

  // Set role-specific styles and content
  if (message.role === "user") {
    messageElement.classList.add("user");
    avatarElement.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
      </svg>
    `;
  } else if (message.role === "assistant" || message.role === "bot") {
    messageElement.classList.add("bot");
    avatarElement.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
        <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
      </svg>
    `;
  } else if (message.role === "system") {
    messageElement.classList.add("system");
    avatarElement.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
      </svg>
    `;
  }

  // Make sure we have content
  const content = message.content || '';

  // Set message content
  bubbleElement.innerHTML = formatMessage(content);

  // Apply syntax highlighting to code blocks
  Array.from(bubbleElement.querySelectorAll('pre code')).forEach(block => {
    hljs.highlightElement(block);
  });

  // Add the message to the chat history
  chatHistory.appendChild(messageElement);

  // Scroll to the bottom
  chatHistory.scrollTop = chatHistory.scrollHeight;

  // For debugging: log the message being rendered
  console.log("Rendered message:", message.role, content.substring(0, 50) + (content.length > 50 ? '...' : ''));
}

function formatMessage(content) {
  if (!content) return "";

  content = content.trim();

  // Process code blocks
  content = content.replace(/```(\w+)?\n([\s\S]+?)```/g, (match, language, code) => {
    const uniqueId = `code-block-${Math.random().toString(36).substring(2, 9)}`;
    const displayLanguage = language || 'text';

    return `
      <div class="code-block" id="${uniqueId}">
        <div class="code-header">
          <div class="code-language">${displayLanguage}</div>
          <button class="copy-button" onclick="copyToClipboard('${uniqueId}')">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span>Copy</span>
          </button>
        </div>
        <pre><code class="language-${displayLanguage}">${escapeHtml(code.trim())}</code></pre>
      </div>
    `;
  });

  // Process <code></code> tags
  content = content.replace(/<code>([\s\S]+?)<\/code>/g, (match, code) => {
    return `<code class="inline-code">${escapeHtml(code)}</code>`;
  });

  // Process thought blocks
  content = content.replace(/<think>([\s\S]*?)<\/think>/g, (match, thinking) => {
    return `
      <div class="thought-block">
        <div class="thought-header">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <span>Thought Analysis</span>
        </div>
        <div class="thought-content">${thinking.trim()}</div>
      </div>
    `;
  });

  // Process bold text
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Process markdown headers
  content = content.replace(/^(#{1,6})\s(.+)$/gm, (match, hashes, content) => {
    const level = hashes.length;
    return `<h${level} class="markdown-header header-${level}">${content}</h${level}>`;
  });

  return content;
}

// Update the handleSendMessage function to handle collection errors
async function handleSendMessage() {
  const message = chatInput.value.trim();

  if (!message || isProcessing || !activeConversationId) return;

  try {
    isProcessing = true;
    toggleLoadingState(true);

    // Clear the input
    chatInput.value = "";
    chatInput.style.height = "auto";

    // Immediately render the user message in the UI
    const userMessage = {
      role: "user",
      content: message,
      timestamp: new Date().toISOString()
    };
    renderMessage(userMessage);

    // Add a typing indicator
    const loadingId = addTypingIndicator();

    // Send the message to the backend
    const response = await fetch(`${API_BASE_URL}/conversations/${activeConversationId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        role: "user",
        content: message
      }),
    });

    // Remove typing indicator
    removeTypingIndicator(loadingId);

    // Process the response
    if (!response.ok) {
      // If there's an error, still show it in the UI
      const errorData = await response.json();
      const errorMessage = errorData.error || "Error processing message";

      const assistantErrorMessage = {
        role: "assistant",
        content: `Error: ${errorMessage}`,
        timestamp: new Date().toISOString()
      };
      renderMessage(assistantErrorMessage);

      throw new Error(errorMessage);
    }

    // Parse the response
    const data = await response.json();

    // Render the assistant's response if it exists
    if (data && data.assistant_message && data.assistant_message.content) {
      const assistantMessage = {
        role: "assistant",
        content: data.assistant_message.content,
        timestamp: data.assistant_message.timestamp || new Date().toISOString()
      };
      renderMessage(assistantMessage);
    }
  } catch (error) {
    console.error("Error sending message:", error);

    // Show error in toast
    showToast(`Error: ${error.message}`, "error");
  } finally {
    isProcessing = false;
    toggleLoadingState(false);
  }
}

function addTypingIndicator() {
  const id = `typing-${Date.now()}`;
  const typingHtml = `
    <div id="${id}" class="message bot">
      <div class="message-avatar">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
          <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
        </svg>
      </div>
      <div class="message-content">
        <div class="message-bubble">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
  `;

  chatHistory.insertAdjacentHTML('beforeend', typingHtml);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  return id;
}

function removeTypingIndicator(id) {
  const element = document.getElementById(id);
  if (element) element.remove();
}

async function handleDebugClick() {
  if (isProcessing) return;

  try {
    isProcessing = true;
    toggleLoadingState(true);
    showToast("Getting collection data...", "info");

    const response = await fetch(`${API_BASE_URL}/debug/collection`);

    if (!response.ok) {
      throw new Error("Error retrieving collection data");
    }

    const data = await response.json();

    // Create a new conversation for debug data
    const conversation = await createNewConversation("Collection Debug");

    // Add the data as a message
    const formattedDebug = `\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;

    await fetch(`${API_BASE_URL}/conversations/${conversation.id}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        role: "system",
        content: "Here is the collection data:\n" + formattedDebug
      }),
    });

    // Reload the conversation to show the new message
    await loadConversation(conversation.id);

    showToast("Collection data retrieved successfully", "success");
  } catch (error) {
    console.error("Debug error:", error);
    showToast(`Error: ${error.message}`, "error");
  } finally {
    isProcessing = false;
    toggleLoadingState(false);
  }
}

// Utility Functions
function toggleLoadingState(isLoading) {
  sendButton.disabled = isLoading;
  chatInput.disabled = isLoading;
  debugButton.disabled = isLoading;
  dropArea.style.opacity = isLoading ? "0.5" : "1";
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function copyToClipboard(blockId) {
  const codeBlock = document.getElementById(blockId);
  const codeContent = codeBlock.querySelector("code").textContent;

  navigator.clipboard.writeText(codeContent)
    .then(() => {
      // Update button temporarily
      const button = codeBlock.querySelector(".copy-button");
      const originalContent = button.innerHTML;

      button.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
        <span>Copied</span>
      `;
      button.classList.add("copied");

      setTimeout(() => {
        button.innerHTML = originalContent;
        button.classList.remove("copied");
      }, 2000);

      showToast("Code copied to clipboard", "success");
    })
    .catch(() => {
      showToast("Error copying code", "error");
    });
}

function showToast(message, type = "info") {
  const toast = document.getElementById("toast");

  // Clear any previous classes
  toast.className = "";

  toast.textContent = message;
  toast.classList.add(type);
  toast.classList.add("show");

  if (type === "success") {
    toast.style.backgroundColor = "#22c55e";
  } else if (type === "error") {
    toast.style.backgroundColor = "#ef4444";
  } else {
    toast.style.backgroundColor = "#2563eb";
  }

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

function updateModelInfo() {
  fetch(`${API_BASE_URL}/.env`)
    .then(response => response.text())
    .then(text => {
      const modelMatch = text.match(/LLM_MODEL=(.+)/);
      if (modelMatch && modelMatch[1]) {
        modelName.textContent = modelMatch[1];
      } else {
        modelName.textContent = DEFAULT_MODEL;
      }
    })
    .catch(() => {
      // Use default if there's an error
      modelName.textContent = DEFAULT_MODEL;
    });
}

// Make copyToClipboard global so it can be called from HTML
window.copyToClipboard = copyToClipboard;