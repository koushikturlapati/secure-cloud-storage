const MAX_STORAGE_BYTES = 10 * 1024 * 1024 * 1024;

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const fileTableBody = document.getElementById("fileTableBody");
const storageStatus = document.getElementById("storageStatus");
const usernameDisplay = document.getElementById("usernameDisplay");
const logoutBtn = document.getElementById("logoutBtn");
const logoutBox = document.getElementById("logoutBox");
const confirmLogoutBtn = document.getElementById("confirmLogoutBtn");
const cancelLogoutBtn = document.getElementById("cancelLogoutBtn");
const fileCount = document.getElementById("fileCount");
const storageProgress = document.getElementById("storageProgress");
const syncStatus = document.getElementById("syncStatus");

const state = {
    files: []
};

function redirectToLogin() { 
    sessionStorage.removeItem("access_token");
    window.location.replace("index.html");
}

function getToken() {
    return sessionStorage.getItem("access_token");
}

function formatBytes(bytes) {
    if (!bytes) return "0.0 MB";
    const units = ["B", "KB", "MB", "GB"];
    let value = bytes;
    let unitIndex = 0;

    while (value >= 1024 && unitIndex < units.length - 1) {
        value /= 1024;
        unitIndex += 1;
    }

    return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function updateStorageStatus() {
    const usedBytes = state.files.reduce((total, file) => total + Number(file.size || 0), 0);
    storageStatus.textContent = `Storage Used ${formatBytes(usedBytes)} / ${formatBytes(MAX_STORAGE_BYTES)}`;
    if (storageProgress) {
        storageProgress.style.width = `${Math.min((usedBytes / MAX_STORAGE_BYTES) * 100, 100)}%`;
    }
    if (fileCount) fileCount.textContent = state.files.length;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderFiles() {
    if (!fileTableBody) return;

    if (!state.files.length) {
        fileTableBody.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state"><strong>Your library is quiet.</strong>Upload a file above to get started.</td>
            </tr>
        `;
        updateStorageStatus();
        return;
    }

    fileTableBody.innerHTML = state.files
        .map(
            (file) => `
                <tr>
                    <td>${escapeHtml(file.name)}</td>
                    <td>${formatBytes(file.size)}</td>
                    <td><span class="file-security">${escapeHtml(file.security || "Encrypted")}</span></td>
                    <td><div class="action-group">
                        <button class="table-action" type="button" data-action="download" data-id="${file.id}">Download</button>
                        <button class="table-action" type="button" data-action="edit" data-id="${file.id}">Rename</button>
                        <button class="table-action" type="button" data-action="delete" data-id="${file.id}">Delete</button>
                    </div>
                    </td>
                </tr>
            `
        )
        .join("");

    updateStorageStatus();
}

function saveFiles() {
    renderFiles();
}

async function loadFiles() {
    const token = getToken();
    const response = await fetch("/files/", {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!response.ok) throw new Error("Could not load files");
    state.files = await response.json();
    renderFiles();
    if (syncStatus) syncStatus.textContent = "Synced";
}

function toggleLogoutBox() {
    if (!logoutBox) return;
    logoutBox.classList.toggle("is-visible");
}

async function confirmLogout() {
    const refreshToken = sessionStorage.getItem("refresh_token");
    if (refreshToken) {
        await fetch("/logout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
    }
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("refresh_token");
    sessionStorage.removeItem("dashboardFiles");
    window.location.replace("index.html");
}

async function fetchCurrentUser() {
    const token = getToken();
    if (!token) {
        redirectToLogin();
        return;
    }

    try {
        const response = await fetch("/me", {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error("Token invalid");
        }

        const user = await response.json();
        if (usernameDisplay && user.username) {
            usernameDisplay.textContent = user.username;
            sessionStorage.setItem("username", user.username);
        }
    } catch (error) {
        console.warn("Could not load current user:", error);
        const savedUsername = sessionStorage.getItem("username") || "User";
        if (usernameDisplay) {
            usernameDisplay.textContent = savedUsername;
        }
    }
}

async function uploadToServer(file) {
    const token = getToken();
    if (!token) {
        redirectToLogin();
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/files/upload", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error("Upload failed");
        }
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function addFiles(files) {
    const selectedFiles = Array.from(files || []);

    for (const file of selectedFiles) {
        try {
            const uploaded = await uploadToServer(file);
            state.files.unshift({
                id: uploaded.file_id,
                name: uploaded.filename,
                size: uploaded.size,
                security: "Encrypted"
            });
            saveFiles();
        } catch (error) {
            console.error("Upload failed:", error);
            window.alert(`Could not upload ${file.name}.`);
        }
    }
}

function handleFileSelection(event) {
    addFiles(event.target.files);
    event.target.value = "";
}

function attachDropHandlers() {
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleFileSelection);

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("is-dragging");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("is-dragging");
        });
    });

    dropZone.addEventListener("drop", (event) => {
        addFiles(event.dataTransfer.files);
    });
}

function attachTableEvents() {
    if (!fileTableBody) return;

    fileTableBody.addEventListener("click", async (event) => {
        const button = event.target.closest("button");
        if (!button) return;

        const { action, id } = button.dataset;
        const file = state.files.find((entry) => String(entry.id) === String(id));

        if (!file) return;

        if (action === "delete") {
            const response = await fetch(`/files/${id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${getToken()}` }
            });
            if (response.ok) {
                state.files = state.files.filter((entry) => String(entry.id) !== String(id));
                saveFiles();
            }
            return;
        }

        if (action === "edit") {
            const newName = window.prompt("Rename file:", file.name);
            if (newName && newName.trim()) {
                const response = await fetch(`/files/${id}`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${getToken()}`
                    },
                    body: JSON.stringify({ filename: newName.trim() })
                });
                if (response.ok) {
                    file.name = newName.trim();
                    saveFiles();
                }
            }
            return;
        }

        if (action === "download") {
            const response = await fetch(`/files/${id}`, {
                headers: { Authorization: `Bearer ${getToken()}` }
            });
            if (response.ok) {
                const blobUrl = URL.createObjectURL(await response.blob());
                const anchor = document.createElement("a");
                anchor.href = blobUrl;
                anchor.download = file.name;
                anchor.click();
                URL.revokeObjectURL(blobUrl);
            }
        }
    });
}

function attachLogoutEvents() {
    if (logoutBtn) {
        logoutBtn.addEventListener("click", toggleLogoutBox);
    }

    if (confirmLogoutBtn) {
        confirmLogoutBtn.addEventListener("click", confirmLogout);
    }

    if (cancelLogoutBtn) {
        cancelLogoutBtn.addEventListener("click", toggleLogoutBox);
    }
}

function initDashboard() {
    const token = getToken();
    if (!token) {
        redirectToLogin();
        return;
    }

    attachDropHandlers();
    attachTableEvents();
    attachLogoutEvents();
    fetchCurrentUser();
    loadFiles().catch((error) => {
        console.error("Could not load files:", error);
        redirectToLogin();
    });
}

window.addEventListener("DOMContentLoaded", initDashboard);

