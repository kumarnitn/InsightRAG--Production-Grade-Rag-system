const API_BASE = "http://localhost:8005";

// DOM elements
const backendStatus = document.getElementById("backend-status");
const fileInput = document.getElementById("file-input");
const uploadZone = document.getElementById("upload-zone");
const ingestedList = document.getElementById("ingested-list");
const queryForm = document.getElementById("query-form");
const queryInput = document.getElementById("query-input");
const btnSubmit = document.getElementById("btn-submit");
const btnReset = document.getElementById("btn-reset");
const chatHistory = document.getElementById("chat-history");

// Stat elements
const statP50 = document.getElementById("stat-p50");
const statP95 = document.getElementById("stat-p95");
const statCost = document.getElementById("stat-cost");
const statCitation = document.getElementById("stat-citation");
const progressCitation = document.getElementById("progress-citation");
const statFailure = document.getElementById("stat-failure");
const statFailureContainer = document.getElementById("stat-failure-container");
const statRequestsSummary = document.getElementById("stat-requests-summary");

// Modal elements
const citationModal = document.getElementById("citation-modal");
const closeModal = document.getElementById("close-modal");
const modalSourceBadge = document.getElementById("modal-source-badge");
const modalScoreBadge = document.getElementById("modal-score-badge");
const modalCitationText = document.getElementById("modal-citation-text");

// Store active documents and citations
let ingestedDocuments = [];
let lastQueryCitations = [];

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    // Refresh icons
    lucide.createIcons();
    
    // Check connection
    checkBackendConnection();
    
    // Setup dropzone events
    setupUploadDropzone();
    
    // Set up form submission
    queryForm.addEventListener("submit", handleQuerySubmit);
    
    // Close modal
    closeModal.addEventListener("click", () => {
        citationModal.classList.remove("active");
    });
    
    // Reset database
    btnReset.addEventListener("click", handleResetPipeline);
});

// 1. Backend Connectivity & Dashboard Telemetry
async function checkBackendConnection() {
    try {
        const response = await fetch(`${API_BASE}/`);
        if (response.ok) {
            updateStatus(true);
            updateDashboardStats();
        } else {
            updateStatus(false);
        }
    } catch (e) {
        updateStatus(false);
    }
}

function updateStatus(isOnline) {
    const dot = backendStatus.querySelector(".status-dot");
    const label = backendStatus.querySelector(".status-label");
    
    if (isOnline) {
        dot.className = "status-dot online";
        label.textContent = "Backend Connected";
        queryInput.disabled = false;
        queryInput.placeholder = "Ask a question about the ingested documents...";
        btnSubmit.disabled = false;
    } else {
        dot.className = "status-dot offline";
        label.textContent = "Backend Offline";
        queryInput.disabled = true;
        queryInput.placeholder = "Waiting for backend connection...";
        btnSubmit.disabled = true;
    }
}

async function updateDashboardStats() {
    try {
        const response = await fetch(`${API_BASE}/api/observability/stats`);
        if (response.ok) {
            const data = await response.json();
            
            // Render Stats
            statP50.textContent = data.p50_latency.toFixed(2);
            statP95.textContent = data.p95_latency.toFixed(2);
            statCost.textContent = data.avg_cost.toFixed(6);
            
            const citationPct = data.avg_citation_coverage;
            statCitation.textContent = citationPct.toFixed(1);
            progressCitation.style.width = `${citationPct}%`;
            
            const failurePct = data.failure_rate;
            statFailure.textContent = failurePct.toFixed(1);
            if (failurePct > 0) {
                statFailureContainer.className = "metric-value text-danger";
            } else {
                statFailureContainer.className = "metric-value text-success";
            }
            
            statRequestsSummary.textContent = `${data.total_requests} total requests processed`;
        }
    } catch (e) {
        console.error("Failed to fetch observability stats: ", e);
    }
}

// 2. Document Ingestion
function setupUploadDropzone() {
    uploadZone.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) handleFileUpload(file);
    });
    
    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.classList.add("dragover");
    });
    
    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("dragover");
    });
    
    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("dragover");
        const file = e.dataTransfer.files[0];
        if (file) handleFileUpload(file);
    });
}

async function handleFileUpload(file) {
    // Show uploading visual feedback
    const uploadIcon = uploadZone.querySelector(".upload-icon");
    const uploadText = uploadZone.querySelector(".upload-text");
    
    const origIconClass = uploadIcon.dataset.lucide;
    const origText = uploadText.innerHTML;
    
    uploadIcon.setAttribute("data-lucide", "loader-2");
    uploadIcon.className = "upload-icon animate-spin";
    uploadText.textContent = `Uploading ${file.name}...`;
    lucide.createIcons();
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const response = await fetch(`${API_BASE}/api/ingest`, {
            method: "POST",
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Add to ingested documents list
            ingestedDocuments.push({
                filename: result.filename,
                chunks: result.chunks_count,
                time: result.ingested_at
            });
            renderIngestedList();
            
            // Trigger quick trace check in stats
            updateDashboardStats();
            
            // Update dropzone UI with success
            uploadIcon.setAttribute("data-lucide", "check-circle-2");
            uploadIcon.className = "upload-icon text-success";
            uploadText.innerHTML = `<span class="text-success">Success!</span> Ingested ${result.chunks_count} chunks.`;
        } else {
            const err = await response.json();
            alert(`Ingestion failed: ${err.detail}`);
            resetDropzoneUI(uploadIcon, uploadText, origIconClass, origText);
        }
    } catch (e) {
        alert(`Ingestion network error: ${e.message}`);
        resetDropzoneUI(uploadIcon, uploadText, origIconClass, origText);
    }
    
    // Auto-restore dropzone after 3.5s
    setTimeout(() => {
        resetDropzoneUI(uploadIcon, uploadText, origIconClass, origText);
    }, 3500);
}

function resetDropzoneUI(icon, textEl, origIcon, origText) {
    icon.setAttribute("data-lucide", "cloud-lightning");
    icon.className = "upload-icon";
    textEl.innerHTML = `Drag & drop files here, or <span class="highlight">browse</span>`;
    lucide.createIcons();
}

function renderIngestedList() {
    if (ingestedDocuments.length === 0) {
        ingestedList.innerHTML = `
            <div class="empty-state">
                <i data-lucide="folder-open"></i>
                <p>No documents ingested yet.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    ingestedList.innerHTML = ingestedDocuments.map(doc => `
        <div class="ingested-item">
            <div class="doc-info">
                <i data-lucide="file-text"></i>
                <span class="doc-name" title="${doc.filename}">${doc.filename}</span>
            </div>
            <span class="chunk-badge">${doc.chunks} chunks</span>
        </div>
    `).join("");
    
    lucide.createIcons();
}

// 3. Q&A and Chat Interface
async function handleQuerySubmit(e) {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;
    
    queryInput.value = "";
    
    // Remove system welcome if present
    const welcome = chatHistory.querySelector(".system-welcome");
    if (welcome) welcome.remove();
    
    // Render User Message
    appendMessage("user", query);
    
    // Render Bot Loading indicator
    const botMsgId = "bot-loading-" + Date.now();
    appendLoadingMessage(botMsgId);
    
    try {
        const response = await fetch(`${API_BASE}/api/query`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ query: query, top_k: 4 })
        });
        
        // Remove loading indicator
        document.getElementById(botMsgId).remove();
        
        if (response.ok) {
            const data = await response.json();
            
            // Update last active citations list
            lastQueryCitations = data.citations;
            
            // Format answer text with inline citation anchors
            const formattedAnswer = formatAnswerCitations(data.answer);
            
            appendMessage("bot", formattedAnswer);
            updateDashboardStats();
        } else {
            const err = await response.json();
            appendMessage("bot", `<div class="text-danger">Error: ${err.detail || "Query failed to execute."}</div>`);
            updateDashboardStats(); // Track the failure rate increment
        }
    } catch (err) {
        document.getElementById(botMsgId).remove();
        appendMessage("bot", `<div class="text-danger">Network Error: ${err.message}</div>`);
        updateDashboardStats();
    }
}

function appendMessage(sender, text) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.innerHTML = sender === "user" ? "U" : `<i data-lucide="bot" style="width:16px;height:16px"></i>`;
    
    const content = document.createElement("div");
    content.className = "bubble-content";
    content.innerHTML = text;
    
    bubble.appendChild(avatar);
    bubble.appendChild(content);
    chatHistory.appendChild(bubble);
    
    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;
    lucide.createIcons();
}

function appendLoadingMessage(id) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble bot`;
    bubble.id = id;
    
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.innerHTML = `<i data-lucide="bot" style="width:16px;height:16px"></i>`;
    
    const content = document.createElement("div");
    content.className = "bubble-content";
    content.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    bubble.appendChild(avatar);
    bubble.appendChild(content);
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    lucide.createIcons();
}

// Convert LLM markdown/brackets [1] into clickable glass tags
function formatAnswerCitations(text) {
    // Match brackets e.g. [1] or [2]
    return text.replace(/\[(\d+)\]/g, (match, idx) => {
        return `<span class="citation-link" onclick="openCitationDetails(${idx})">${idx}</span>`;
    });
}

window.openCitationDetails = function(idx) {
    const citation = lastQueryCitations.find(c => c.citation_index === parseInt(idx));
    
    if (citation) {
        modalSourceBadge.textContent = citation.source;
        modalScoreBadge.textContent = `Relevance: ${Math.round(citation.score * 100)}%`;
        modalCitationText.textContent = citation.text;
        
        citationModal.classList.add("active");
    } else {
        alert(`Source citation [${idx}] details were not returned or verified in this query session.`);
    }
};

// 4. Reset DB & Observability Stats
async function handleResetPipeline() {
    if (!confirm("Are you sure you want to reset the vector database and monitoring stats? This action is irreversible.")) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/observability/reset`, {
            method: "POST"
        });
        
        if (response.ok) {
            ingestedDocuments = [];
            lastQueryCitations = [];
            renderIngestedList();
            
            chatHistory.innerHTML = `
                <div class="system-welcome">
                    <div class="welcome-icon"><i data-lucide="bot"></i></div>
                    <h3>Welcome to Antigravity RAG</h3>
                    <p>Once you ingest documents on the left, query the system here. The generation is strictly grounded in retrieved evidence with citation links.</p>
                </div>
            `;
            lucide.createIcons();
            
            // Clear stats on UI
            updateDashboardStats();
            alert("RAG vector store and metrics successfully reset.");
        } else {
            alert("Failed to reset vector pipeline database.");
        }
    } catch (e) {
        alert(`Reset error: ${e.message}`);
    }
}
