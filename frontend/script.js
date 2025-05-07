// Constants
const API_BASE_URL = "http://localhost:5000"; // Point to the correct backend URL
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
const currentConversationTitle = document.getElementById(
  "current-conversation-title"
);
const editTitleBtn = document.getElementById("edit-title-btn");
const editTitleModal = document.getElementById("edit-title-modal");
const editTitleInput = document.getElementById("edit-title-input");
const saveEditTitleBtn = document.getElementById("save-edit-title");
const cancelEditTitleBtn = document.getElementById("cancel-edit-title");
const conversationDocuments = document.getElementById("conversation-documents");
const viewIndexBtn = document.getElementById("view-index-btn");
const indexModal = document.getElementById("index-modal");
const closeIndexModal = document.getElementById("close-index-modal");
const indexContent = document.getElementById("index-content");
const documentsPanel = document.getElementById("documents-panel");
const viewDocumentsBtn = document.getElementById("view-documents-btn");
const documentsList = document.getElementById("documents-list");
const documentContentModal = document.getElementById("document-content-modal");
const documentContentTitle = document.getElementById("document-content-title");
const documentContent = document.getElementById("document-content");
const closeDocumentContent = document.getElementById("close-document-content");
const documentAnalysisModal = document.getElementById(
  "document-analysis-modal"
);
const documentAnalysisTitle = document.getElementById(
  "document-analysis-title"
);
const documentAnalysis = document.getElementById("document-analysis");
const closeDocumentAnalysis = document.getElementById(
  "close-document-analysis"
);

// Templates
const conversationTemplate = document.getElementById("conversation-template");
const messageTemplate = document.getElementById("message-template");

// State
let activeConversationId = null;
let isProcessing = false;
let isInitialLoad = true;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadConversations();
  updateModelInfo();
});

// Event Listeners
let dragCounter = 0;
let isDraggingFile = false;

// This is a completely fresh, minimal implementation

// Add these at the top of your script.js file
let dragActive = false;

// Replace your entire setupEventListeners function with this simpler version
function setupEventListeners() {
  // Toggle sidebar
  toggleSidebarBtn.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
  });

  // ==== SIMPLIFIED DRAG AND DROP ====
  // Document-level drag events
  document.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (!dragActive) {
      dragActive = true;
      if (dropOverlay) {
        dropOverlay.style.display = "flex";
      }
    }
  });

  document.addEventListener("dragleave", (e) => {
    // Only consider leaving if we're leaving the window
    if (
      e.clientX <= 0 ||
      e.clientX >= window.innerWidth ||
      e.clientY <= 0 ||
      e.clientY >= window.innerHeight
    ) {
      dragActive = false;
      if (dropOverlay) {
        dropOverlay.style.display = "none";
      }
    }
  });

  document.addEventListener("drop", (e) => {
    e.preventDefault();
    dragActive = false;

    if (dropOverlay) {
      dropOverlay.style.display = "none";
    }

    console.log("Drop event detected with files:", e.dataTransfer);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      console.log("File to upload:", file.name, file.size, file.type);
      uploadFile(file);
    } else {
      console.warn("No files found in drop event");
    }
  });

  // Drop overlay events
  if (dropOverlay) {
    dropOverlay.addEventListener("dragover", (e) => {
      e.preventDefault();
    });

    dropOverlay.addEventListener("drop", (e) => {
      e.preventDefault();
      dragActive = false;
      dropOverlay.style.display = "none";

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        uploadFile(e.dataTransfer.files[0]);
      }
    });
  }

  // Drop area in sidebar
  if (dropArea) {
    dropArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropArea.classList.add("border-blue-500");
      dropArea.classList.add("bg-blue-50");
    });

    dropArea.addEventListener("dragleave", (e) => {
      dropArea.classList.remove("border-blue-500");
      dropArea.classList.remove("bg-blue-50");
    });

    dropArea.addEventListener("drop", (e) => {
      e.preventDefault();
      dragActive = false;

      dropArea.classList.remove("border-blue-500");
      dropArea.classList.remove("bg-blue-50");

      if (dropOverlay) {
        dropOverlay.style.display = "none";
      }

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        uploadFile(e.dataTransfer.files[0]);
      }
    });
  }
  // ==== END DRAG AND DROP ====

  // File input
  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        uploadFile(e.target.files[0]);
      }
    });
  }

  // The rest of your event listeners...
  // Chat input handling
  if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    chatInput.addEventListener("input", () => {
      chatInput.style.height = "auto";
      chatInput.style.height = Math.min(chatInput.scrollHeight, 128) + "px";
    });
  }

  // Buttons
  if (sendButton) {
    sendButton.addEventListener("click", handleSendMessage);
  }

  if (debugButton) {
    debugButton.addEventListener("click", handleDebugClick);
  }

  if (newChatButton) {
    newChatButton.addEventListener("click", () =>
      createNewConversation("New Conversation", false)
    );
  }

  // Edit title functionality
  if (editTitleBtn && editTitleModal && editTitleInput) {
    editTitleBtn.addEventListener("click", () => {
      if (activeConversationId) {
        editTitleInput.value = currentConversationTitle.textContent.trim();
        editTitleModal.style.display = "flex";
        editTitleInput.focus();
      }
    });

    if (saveEditTitleBtn) {
      saveEditTitleBtn.addEventListener("click", async () => {
        const newTitle = editTitleInput.value.trim();
        if (newTitle && activeConversationId) {
          await updateConversationTitle(activeConversationId, newTitle);
          editTitleModal.style.display = "none";
        }
      });
    }

    if (cancelEditTitleBtn) {
      cancelEditTitleBtn.addEventListener("click", () => {
        editTitleModal.style.display = "none";
      });
    }

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

  // Index modal event listeners
  viewIndexBtn.addEventListener("click", showIndexModal);
  closeIndexModal.addEventListener("click", hideIndexModal);
  indexModal.addEventListener("click", (e) => {
    if (e.target === indexModal) {
      hideIndexModal();
    }
  });

  // Documents panel toggle
  viewDocumentsBtn.addEventListener("click", async () => {
    const isHidden = documentsPanel.classList.contains("hidden");
    documentsPanel.classList.toggle("hidden");

    if (isHidden && activeConversationId) {
      // Load and display documents when panel is opened
      try {
        const response = await fetch(
          `${API_BASE_URL}/conversations/${activeConversationId}`
        );
        if (!response.ok) {
          throw new Error("Failed to load conversation");
        }
        const conversation = await response.json();
        if (conversation && conversation.documents) {
          renderConversationDocuments(conversation.documents);
        }
      } catch (error) {
        console.error("Error loading documents:", error);
        showToast(`Error loading documents: ${error.message}`, "error");
      }
    }
  });

  // Close documents panel
  const closeDocumentsPanel = document.getElementById("close-documents-panel");
  if (closeDocumentsPanel) {
    closeDocumentsPanel.addEventListener("click", () => {
      documentsPanel.classList.add("hidden");
    });
  }

  // Document content modal
  closeDocumentContent.addEventListener("click", () => {
    documentContentModal.classList.add("hidden");
  });

  documentContentModal.addEventListener("click", (e) => {
    if (e.target === documentContentModal) {
      documentContentModal.classList.add("hidden");
    }
  });

  // Document analysis modal
  closeDocumentAnalysis.addEventListener("click", () => {
    documentAnalysisModal.classList.add("hidden");
  });

  documentAnalysisModal.addEventListener("click", (e) => {
    if (e.target === documentAnalysisModal) {
      documentAnalysisModal.classList.add("hidden");
    }
  });
}

// Drag and Drop Event Handlers
function handleDragEnter(e) {
  e.preventDefault();

  // Check if actually dragging a file
  if (
    e.dataTransfer.types &&
    (e.dataTransfer.types.includes("Files") ||
      e.dataTransfer.types.indexOf("Files") !== -1)
  ) {
    isDraggingFile = true;
    dragCounter++;

    // Only show the overlay when we detect a file is being dragged
    if (dropOverlay && dragCounter === 1) {
      dropOverlay.style.display = "flex";
    }
  }
}

function handleDragLeave(e) {
  e.preventDefault();

  if (isDraggingFile) {
    dragCounter--;

    // Only hide when we've left the document completely
    if (dragCounter <= 0) {
      dragCounter = 0; // Ensure we don't get negative values
      if (dropOverlay) {
        dropOverlay.style.display = "none";
      }
    }
  }
}

function handleDragOver(e) {
  e.preventDefault();

  if (isDraggingFile) {
    // Keep the overlay visible
    if (dropOverlay) {
      dropOverlay.style.display = "flex";
    }
  }
  return false;
}

function handleDrop(e) {
  e.preventDefault();

  if (isDraggingFile) {
    isDraggingFile = false;
    dragCounter = 0;

    if (dropOverlay) {
      dropOverlay.style.display = "none";
    }

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  }
  return false;
}

// Drop Area specific handlers
function handleDropAreaEnter(e) {
  e.preventDefault();
  e.stopPropagation();

  if (isDraggingFile) {
    dropArea.classList.add("border-blue-500");
    dropArea.classList.add("bg-blue-50");
  }
  return false;
}

function handleDropAreaLeave(e) {
  e.preventDefault();
  e.stopPropagation();

  dropArea.classList.remove("border-blue-500");
  dropArea.classList.remove("bg-blue-50");
  return false;
}

function handleDropAreaOver(e) {
  e.preventDefault();
  e.stopPropagation();

  if (isDraggingFile) {
    dropArea.classList.add("border-blue-500");
    dropArea.classList.add("bg-blue-50");
  }
  return false;
}

function handleDropAreaDrop(e) {
  e.preventDefault();
  e.stopPropagation();

  dropArea.classList.remove("border-blue-500");
  dropArea.classList.remove("bg-blue-50");

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    uploadFile(files[0]);
  }
  return false;
}

// Update preventDefaults function
function preventDefaults(e) {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }
  return false;
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
    console.log(
      "Fetching conversations from:",
      `${API_BASE_URL}/conversations`
    );
    const response = await fetch(`${API_BASE_URL}/conversations`);

    if (!response.ok) {
      console.error("Error response:", response.status, response.statusText);
      throw new Error("Failed to load conversations");
    }

    const data = await response.json();
    console.log("Loaded conversations data:", data);

    // If there are conversations available
    if (data.conversations && data.conversations.length > 0) {
      console.log(`Found ${data.conversations.length} conversations`);
      // Set the first conversation as active if none is active
      if (!activeConversationId) {
        activeConversationId = data.conversations[0].id;
        console.log("Set active conversation to:", activeConversationId);
      }

      renderConversationsList(data.conversations);
      await loadConversation(activeConversationId);
    } else {
      console.log("No conversations found, creating a new one");
      // Create a new conversation if none exist
      await createNewConversation("New Conversation", true);
    }

    isInitialLoad = false;
  } catch (error) {
    console.error("Error loading conversations:", error);
    showToast(`Error loading conversations: ${error.message}`, "error");

    // Create a new conversation if we couldn't load any
    if (!activeConversationId) {
      await createNewConversation("New Conversation", true);
    }

    isInitialLoad = false;
  }
}

async function loadConversation(conversationId) {
  if (!conversationId) return;

  try {
    const response = await fetch(
      `${API_BASE_URL}/conversations/${conversationId}`
    );

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

async function createNewConversation(
  title = "New Conversation",
  skipReload = false
) {
  try {
    // Ensure title is a string
    if (typeof title !== "string") {
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
        initial_message: "Hello! How can I help you with your code?",
      }),
    });

    if (!response.ok) {
      throw new Error("Failed to create new conversation");
    }

    const conversation = await response.json();
    activeConversationId = conversation.id;

    // Reload conversations to update the list - but not if we're already in the load process
    if (!skipReload) {
      await loadConversations();
    } else {
      // Render the new conversation directly
      renderConversation(conversation);
    }

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
      await createNewConversation("New Conversation", true);
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
        title: newTitle,
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
  console.log("Rendering conversations list:", conversations);

  conversations.forEach((conversation) => {
    const conversationNode = conversationTemplate.content.cloneNode(true);
    const conversationItem =
      conversationNode.querySelector(".conversation-item");
    const titleElement = conversationNode.querySelector(".conversation-title");
    const deleteButton = conversationNode.querySelector(".delete-conversation");

    // Asegurarse de que id esté definido
    if (!conversation.id) {
      console.error("Conversation missing ID:", conversation);
      return;
    }

    conversationItem.dataset.id = conversation.id;
    titleElement.textContent = conversation.title || "Untitled";

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
      input.value = conversation.title || "Untitled";
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
    conversation.messages.forEach((message) => {
      renderMessage(message);
    });
  }

  // Render associated documents
  renderConversationDocuments(conversation.documents || []);

  // Scroll to bottom
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function deleteDocument(conversationId, documentId, event) {
  // Prevent event propagation
  event.stopPropagation();

  try {
    const response = await fetch(
      `${API_BASE_URL}/conversations/${conversationId}/documents/${documentId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error("Failed to delete document");
    }

    // Reload the active conversation to refresh the documents list
    await loadConversation(conversationId);

    showToast("Document deleted successfully", "success");
  } catch (error) {
    console.error("Error deleting document:", error);
    showToast(`Error deleting document: ${error.message}`, "error");
  }
}

function renderConversationDocuments(documents) {
  // Clear current documents
  conversationDocuments.innerHTML = "";
  documentsList.innerHTML = "";

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
  documents.forEach((doc) => {
    // Add to conversation documents (compact view)
    const template = document.getElementById("document-template");
    const docNode = template.content.cloneNode(true);
    const docItem = docNode.querySelector(".document-item");
    const docName = docNode.querySelector(".document-name");
    const docInfo = docNode.querySelector(".document-info");
    const viewDocBtn = docNode.querySelector(".view-document-btn");
    const viewAnalysisBtn = docNode.querySelector(".view-analysis-btn");
    const deleteButton = docNode.querySelector(".delete-document");

    docName.textContent = doc.filename;
    docInfo.textContent = `Type: ${doc.file_type || "unknown"}`;

    // Store document ID as a data attribute
    docItem.dataset.id = doc.id;

    // Add event listeners
    viewDocBtn.addEventListener("click", () => {
      showDocumentContent(doc);
    });

    viewAnalysisBtn.addEventListener("click", () => {
      showDocumentAnalysis(doc);
    });

    if (deleteButton) {
      deleteButton.addEventListener("click", (event) => {
        deleteDocument(activeConversationId, doc.id, event);
      });
    }

    documentsList.appendChild(docNode);
  });
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

  // Make sure we have content
  const content = message.content || "";

  // Set role-specific styles and content
  if (message.role === "user") {
    messageElement.classList.add("user");
    avatarElement.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
      </svg>
    `;

    // Set message content as plain text for user messages
    bubbleElement.textContent = content;
  } else if (message.role === "assistant" || message.role === "bot") {
    messageElement.classList.add("bot");
    avatarElement.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
        <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
      </svg>
    `;

    // Set message content with formatting for assistant messages
    bubbleElement.innerHTML = formatMessage(content);
  } else if (message.role === "system") {
    messageElement.classList.add("system");
    avatarElement.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
      </svg>
    `;

    // Set message content with formatting for system messages
    bubbleElement.innerHTML = formatMessage(content);
  }

  // Apply syntax highlighting to code blocks (only needed for assistant and system messages)
  if (message.role !== "user") {
    Array.from(bubbleElement.querySelectorAll("pre code")).forEach((block) => {
      hljs.highlightElement(block);
    });
  }

  // Add the message to the chat history
  chatHistory.appendChild(messageElement);

  // Scroll to the bottom
  chatHistory.scrollTop = chatHistory.scrollHeight;

  // For debugging: log the message being rendered
  console.log(
    "Rendered message:",
    message.role,
    content.substring(0, 50) + (content.length > 50 ? "..." : "")
  );
}

function formatMessage(content) {
  if (!content) return "";

  content = content.trim();

  // First, protect code blocks from other replacements by tokenizing them
  const codeBlocks = [];
  content = content.replace(
    /```(\w+)?\n([\s\S]+?)```/g,
    (match, language, code) => {
      const token = `___CODE_BLOCK_${codeBlocks.length}___`;
      codeBlocks.push({
        language: language || "text",
        code: code.trim(),
      });
      return token;
    }
  );

  // Process inline code with single backticks (protect from other replacements)
  const inlineCodeBlocks = [];
  content = content.replace(/`([^`]+)`/g, (match, code) => {
    const token = `___INLINE_CODE_${inlineCodeBlocks.length}___`;
    inlineCodeBlocks.push(code);
    return token;
  });

  // Process thought blocks
  content = content.replace(
    /<think>([\s\S]*?)<\/think>/g,
    (match, thinking) => {
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
    }
  );

  // Process bullet lists (with proper indentation and spacing)
  const bulletListLines = content.split("\n");
  let inBulletList = false;
  let bulletListHTML = "";
  let processedLines = [];

  for (let i = 0; i < bulletListLines.length; i++) {
    const line = bulletListLines[i];

    // Check if the line is a bullet point
    if (line.trim().match(/^-\s+.+/)) {
      // Start a new list if we're not already in one
      if (!inBulletList) {
        bulletListHTML = '<ul class="readable-list">';
        inBulletList = true;
      }

      // Add the bullet point as a list item
      const itemContent = line.trim().substring(1).trim();
      bulletListHTML += `<li class="readable-item">${itemContent}</li>`;
    } else {
      // If we were in a list and now we're not, close the list
      if (inBulletList) {
        bulletListHTML += "</ul>";
        processedLines.push(bulletListHTML);
        bulletListHTML = "";
        inBulletList = false;
      }

      // Add the non-bullet line
      processedLines.push(line);
    }
  }

  // Close any open list at the end
  if (inBulletList) {
    bulletListHTML += "</ul>";
    processedLines.push(bulletListHTML);
  }

  content = processedLines.join("\n");

  // Process numbered lists
  content = content.replace(/^(\d+)\.\s+(.+)$/gm, (match, number, text) => {
    return `<div class="numbered-item"><span class="number">${number}.</span> <span class="content">${text}</span></div>`;
  });

  // Process markdown headers
  content = content.replace(/^(#{1,6})\s(.+)$/gm, (match, hashes, content) => {
    const level = hashes.length;
    return `<h${level} class="readable-header header-${level}">${content}</h${level}>`;
  });

  // Process paragraphs (add proper spacing between paragraphs)
  content = content.replace(/(.+)\n\n(.+)/g, (match, para1, para2) => {
    // Don't process if the paragraph is already in an HTML tag
    if (
      para1.includes("<div") ||
      para1.includes("<ul") ||
      para1.includes("<p") ||
      para2.includes("<div") ||
      para2.includes("<ul") ||
      para2.includes("<p")
    ) {
      return match;
    }
    return `<p class="readable-paragraph">${para1}</p>\n\n<p class="readable-paragraph">${para2}</p>`;
  });

  // Process <code></code> tags
  content = content.replace(/<code>([\s\S]+?)<\/code>/g, (match, code) => {
    return `<code class="inline-code">${escapeHtml(code)}</code>`;
  });

  // Process bold text
  content = content.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Process italics
  content = content.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // Process horizontal rules
  content = content.replace(/^---+$/gm, '<hr class="readable-hr">');

  // Restore inline code blocks with proper formatting
  inlineCodeBlocks.forEach((code, i) => {
    content = content.replace(
      `___INLINE_CODE_${i}___`,
      `<span class="filename">${escapeHtml(code)}</span>`
    );
  });

  // Whenever there is a hyphen, add a line jump
  content = content.replace(/\s+-\s+/g, "<br>- ");

  // Restore code blocks with proper formatting
  codeBlocks.forEach((block, i) => {
    const uniqueId = `code-block-${Math.random().toString(36).substring(2, 9)}`;
    content = content.replace(
      `___CODE_BLOCK_${i}___`,
      `
      <div class="code-block" id="${uniqueId}">
        <div class="code-header">
          <div class="code-language">${block.language}</div>
          <button class="copy-button" onclick="copyToClipboard('${uniqueId}')">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span>Copy</span>
          </button>
        </div>
        <pre><code class="language-${block.language}">${escapeHtml(
        block.code
      )}</code></pre>
      </div>
    `
    );
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
      timestamp: new Date().toISOString(),
    };
    renderMessage(userMessage);

    // Add a typing indicator
    const loadingId = addTypingIndicator();

    // Send the message to the backend
    const response = await fetch(
      `${API_BASE_URL}/conversations/${activeConversationId}/messages`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          role: "user",
          content: message,
        }),
      }
    );

    // Process the response
    let errorMessage = null;
    let data = null;

    try {
      data = await response.json();
    } catch (parseError) {
      console.error("Error parsing response:", parseError);
      errorMessage = "Error parsing server response";
    }

    // Remove typing indicator
    removeTypingIndicator(loadingId);

    if (!response.ok) {
      // If there's an error, check if it's a model download issue
      if (data && data.error) {
        const error = data.error.toLowerCase();

        // Check if the error is related to Ollama model download
        if (error.includes("downloading") || error.includes("pulling model")) {
          // Show a model download indicator instead of an error
          const modelId = addModelDownloadIndicator();

          showToast(
            "Downloading AI model. This may take several minutes for the first time.",
            "info",
            10000
          );

          // Poll the server every 3 seconds to check if the model download is complete
          const pollInterval = setInterval(async () => {
            try {
              const statusResponse = await fetch(`${API_BASE_URL}/health`);
              const statusData = await statusResponse.json();

              if (statusData.status === "healthy") {
                clearInterval(pollInterval);
                removeModelDownloadIndicator(modelId);

                // Try again automatically
                await handleSendMessage();
              }
            } catch (pollError) {
              console.error("Error polling server status:", pollError);
            }
          }, 3000);

          return;
        }

        errorMessage = data.error;
      } else {
        errorMessage = `Server error (${response.status}): ${response.statusText}`;
      }

      // Display error in chat
      const assistantErrorMessage = {
        role: "assistant",
        content: `Error: ${errorMessage}. Please try again or check the server logs.`,
        timestamp: new Date().toISOString(),
      };
      renderMessage(assistantErrorMessage);

      throw new Error(errorMessage);
    }

    // Handle success case
    if (data) {
      // Render the assistant's response if it exists
      if (data.assistant_message && data.assistant_message.content) {
        const assistantMessage = {
          role: "assistant",
          content: data.assistant_message.content,
          timestamp:
            data.assistant_message.timestamp || new Date().toISOString(),
        };
        renderMessage(assistantMessage);
      } else if (data.error) {
        // Handle case when there's an error in generating AI response
        const errorContent = data.error.includes("model")
          ? `${data.error}. The AI model might be downloading or not available.`
          : data.error;

        const assistantErrorMessage = {
          role: "assistant",
          content: `Error: ${errorContent}`,
          timestamp: new Date().toISOString(),
        };
        renderMessage(assistantErrorMessage);

        // Show error in toast with extended duration
        showToast(`Error: ${errorContent}`, "error", 8000);
      }
    }
  } catch (error) {
    console.error("Error sending message:", error);

    // Show error in toast
    showToast(`Error: ${error.message}`, "error", 5000);
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

  chatHistory.insertAdjacentHTML("beforeend", typingHtml);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  return id;
}

function addModelDownloadIndicator() {
  const id = `model-download-${Date.now()}`;
  const downloadHtml = `
    <div id="${id}" class="message bot">
      <div class="message-avatar">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
          <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
        </svg>
      </div>
      <div class="message-content">
        <div class="message-bubble">
          <div class="model-download-container">
            <div class="download-icon">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </div>
            <p>Downloading AI model...</p>
            <div class="progress-container">
              <div class="progress-bar animate-pulse"></div>
            </div>
            <p class="text-xs mt-2">This may take several minutes. Please wait.</p>
          </div>
        </div>
      </div>
    </div>
  `;

  chatHistory.insertAdjacentHTML("beforeend", downloadHtml);
  chatHistory.scrollTop = chatHistory.scrollHeight;

  return id;
}

function removeModelDownloadIndicator(id) {
  const element = document.getElementById(id);
  if (element) element.remove();
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
    const conversation = await createNewConversation("Collection Debug", false);

    // Add the data as a message
    const formattedDebug = `\`\`\`json\n${JSON.stringify(
      data,
      null,
      2
    )}\n\`\`\``;

    await fetch(`${API_BASE_URL}/conversations/${conversation.id}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        role: "system",
        content: "Here is the collection data:\n" + formattedDebug,
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

  navigator.clipboard
    .writeText(codeContent)
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

function showToast(message, type = "info", duration = 3000) {
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
  }, duration);
}

function updateModelInfo() {
  fetch(`${API_BASE_URL}/health`)
    .then((response) => response.json())
    .then((data) => {
      if (data && data.environment && data.environment.LLM_MODEL) {
        modelName.textContent = data.environment.LLM_MODEL;
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

async function showIndexModal() {
  if (!activeConversationId) {
    showToast("No active conversation", "error");
    return;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/conversations/${activeConversationId}/index`
    );

    if (!response.ok) {
      throw new Error("Failed to load index");
    }

    const data = await response.json();

    // Convert markdown to HTML using marked.js
    const content = marked.parse(data.content);

    // Display the content
    indexContent.innerHTML = content;

    // Initialize Mermaid diagrams if present
    if (window.mermaid) {
      window.mermaid.init(undefined, document.querySelectorAll(".mermaid"));
    }

    // Show the modal
    indexModal.classList.remove("hidden");
  } catch (error) {
    console.error("Error loading index:", error);
    showToast(`Error loading index: ${error.message}`, "error");
  }
}

function hideIndexModal() {
  indexModal.classList.add("hidden");
  indexContent.innerHTML = "";
}

// Add new functions for document handling
async function showDocumentContent(doc) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/conversations/${activeConversationId}/documents/${doc.id}/content`
    );

    if (!response.ok) {
      throw new Error("Failed to load document content");
    }

    const data = await response.json();

    documentContentTitle.textContent = doc.filename;

    // Handle index.md specially
    if (doc.filename === "index.md") {
      documentContent.innerHTML = marked.parse(data.content);
    } else {
      documentContent.textContent = data.content;
      // Apply syntax highlighting if it's a code file
      if (doc.file_type && doc.file_type.match(/\.(js|py|html|css|json)$/)) {
        hljs.highlightElement(documentContent);
      }
    }

    documentContentModal.classList.remove("hidden");
  } catch (error) {
    console.error("Error loading document content:", error);
    showToast(`Error loading document content: ${error.message}`, "error");
  }
}

async function showDocumentAnalysis(doc) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/conversations/${activeConversationId}/documents/${doc.id}/analysis`
    );

    if (!response.ok) {
      throw new Error("Failed to load document analysis");
    }

    const data = await response.json();

    documentAnalysisTitle.textContent = `Analysis: ${doc.filename}`;

    // Convert the analysis to markdown
    let analysisContent = "## Document Analysis\n\n";

    // Add hierarchy if available
    if (data.hierarchy) {
      analysisContent += "### Hierarchy\n\n";
      if (data.hierarchy.layer) {
        analysisContent += `- **Layer:** ${data.hierarchy.layer}\n`;
      }
      if (data.hierarchy.parents && data.hierarchy.parents.length > 0) {
        analysisContent += `- **Parents:** ${data.hierarchy.parents.join(
          ", "
        )}\n`;
      }
      if (data.hierarchy.children && data.hierarchy.children.length > 0) {
        analysisContent += `- **Children:** ${data.hierarchy.children.join(
          ", "
        )}\n`;
      }
      if (
        data.hierarchy.dependencies &&
        data.hierarchy.dependencies.length > 0
      ) {
        analysisContent += `- **Dependencies:** ${data.hierarchy.dependencies.join(
          ", "
        )}\n`;
      }
      analysisContent += "\n";
    }

    // Add summary if available
    if (data.summary) {
      analysisContent += "### Summary\n\n";
      if (data.summary.purpose) {
        analysisContent += `**Purpose:** ${data.summary.purpose}\n\n`;
      }
      if (data.summary.components && data.summary.components.length > 0) {
        analysisContent += "**Components:**\n";
        data.summary.components.forEach((comp) => {
          analysisContent += `- ${comp}\n`;
        });
        analysisContent += "\n";
      }
      if (data.summary.patterns && data.summary.patterns.length > 0) {
        analysisContent += "**Patterns:**\n";
        data.summary.patterns.forEach((pattern) => {
          analysisContent += `- ${pattern}\n`;
        });
        analysisContent += "\n";
      }
    }

    // Add SWOT analysis if available
    if (data.swot) {
      analysisContent += "### SWOT Analysis\n\n";
      if (data.swot.strengths && data.swot.strengths.length > 0) {
        analysisContent += "**Strengths:**\n";
        data.swot.strengths.forEach((s) => {
          analysisContent += `- ${s}\n`;
        });
        analysisContent += "\n";
      }
      if (data.swot.weaknesses && data.swot.weaknesses.length > 0) {
        analysisContent += "**Weaknesses:**\n";
        data.swot.weaknesses.forEach((w) => {
          analysisContent += `- ${w}\n`;
        });
        analysisContent += "\n";
      }
      if (data.swot.opportunities && data.swot.opportunities.length > 0) {
        analysisContent += "**Opportunities:**\n";
        data.swot.opportunities.forEach((o) => {
          analysisContent += `- ${o}\n`;
        });
        analysisContent += "\n";
      }
      if (data.swot.threats && data.swot.threats.length > 0) {
        analysisContent += "**Threats:**\n";
        data.swot.threats.forEach((t) => {
          analysisContent += `- ${t}\n`;
        });
        analysisContent += "\n";
      }
    }

    // Add relationships if available
    if (data.relationships && data.relationships.length > 0) {
      analysisContent += "### Relationships\n\n";
      data.relationships.forEach((rel) => {
        analysisContent += `- **${rel.type}:** ${rel.name}\n`;
        if (rel.description) {
          analysisContent += `  - ${rel.description}\n`;
        }
      });
    }

    documentAnalysis.innerHTML = marked.parse(analysisContent);
    documentAnalysisModal.classList.remove("hidden");
  } catch (error) {
    console.error("Error loading document analysis:", error);
    showToast(`Error loading document analysis: ${error.message}`, "error");
  }
}
