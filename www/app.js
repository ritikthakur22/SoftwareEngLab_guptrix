const base = "/api";
const storageKey = "notes_vault_session";

const state = {
  token: null,
  user: null,
  notes: [],
  noteCategories: new Map(),
  searchQuery: "",
  sortMode: "updated_desc",
  pinFilter: "all",
  categoryFilter: "",
  pendingDeleteId: null,
  pendingDeleteTitle: "",
};

// ─── DOM References ─────────────────────────────
const dom = {
  authPanel: document.getElementById("auth_panel"),
  dashboard: document.getElementById("dashboard"),
  sessionBadge: document.getElementById("session_badge"),
  welcomeTitle: document.getElementById("welcome_title"),
  authStatus: document.getElementById("auth_status"),
  registerForm: document.getElementById("register_form"),
  loginForm: document.getElementById("login_form"),
  noteForm: document.getElementById("note_form"),
  notesList: document.getElementById("notes_list"),
  notesEmpty: document.getElementById("notes_empty"),
  notesSkeleton: document.getElementById("notes_skeleton"),
  searchInput: document.getElementById("search_q"),
  editDialog: document.getElementById("edit_dialog"),
  editForm: document.getElementById("edit_form"),
  editNoteId: document.getElementById("edit_note_id"),
  editTitle: document.getElementById("edit_title"),
  editContent: document.getElementById("edit_content"),
  editCategories: document.getElementById("edit_categories"),
  editColor: document.getElementById("edit_color"),
  editPinned: document.getElementById("edit_pinned"),
  noteTitle: document.getElementById("note_title"),
  noteContent: document.getElementById("note_content"),
  noteCategories: document.getElementById("note_categories"),
  noteColor: document.getElementById("note_color"),
  notePinned: document.getElementById("note_pinned"),
  btnLogout: document.getElementById("btn_logout"),
  btnSearch: document.getElementById("btn_search"),
  btnClearSearch: document.getElementById("btn_clear_search"),
  noteTemplate: document.getElementById("note_template"),
  toastContainer: document.getElementById("toast_container"),
  noteCountBadge: document.getElementById("note_count_badge"),
  statTotal: document.getElementById("stat_total"),
  statPinned: document.getElementById("stat_pinned"),
  statCategories: document.getElementById("stat_categories"),
  sortNotes: document.getElementById("sort_notes"),
  filterPin: document.getElementById("filter_pin"),
  categoryFilters: document.getElementById("category_filters"),
  // Password strength
  regPassword: document.getElementById("reg_password"),
  strengthMeter: document.getElementById("strength_meter"),
  strengthLabel: document.getElementById("strength_label"),
  // Confirm dialog
  confirmDialog: document.getElementById("confirm_dialog"),
  confirmMessage: document.getElementById("confirm_message"),
  btnConfirmCancel: document.getElementById("btn_confirm_cancel"),
  btnConfirmDelete: document.getElementById("btn_confirm_delete"),
  // Export/Import
  btnExport: document.getElementById("btn_export"),
  btnImport: document.getElementById("btn_import"),
  importFile: document.getElementById("import_file"),
  // Sidebar
  sidebar: document.getElementById("sidebar"),
  sidebarOverlay: document.getElementById("sidebar_overlay"),
  hamburgerBtn: document.getElementById("hamburger_btn"),
  sidebarCloseBtn: document.getElementById("sidebar_close_btn"),
  // Nav items
  navNotes: document.getElementById("nav_notes"),
  navExport: document.getElementById("nav_export"),
  navImport: document.getElementById("nav_import"),
  navShortcuts: document.getElementById("nav_shortcuts"),
};

// ─── Toast Notification System ──────────────────
function showToast(message, type = "info", duration = 4000) {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.style.setProperty("--toast-duration", `${duration}ms`);

  const icons = {
    success: "✓",
    error: "✕",
    info: "ℹ",
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-dismiss" aria-label="Dismiss">×</button>
    <div class="toast-progress"></div>
  `;

  const dismiss = toast.querySelector(".toast-dismiss");
  dismiss.addEventListener("click", () => removeToast(toast));

  dom.toastContainer.appendChild(toast);

  const autoRemove = setTimeout(() => removeToast(toast), duration);
  toast._autoRemove = autoRemove;

  // Limit to 5 visible toasts
  const toasts = dom.toastContainer.querySelectorAll(".toast:not(.removing)");
  if (toasts.length > 5) {
    removeToast(toasts[0]);
  }
}

function removeToast(toast) {
  if (toast._removed) return;
  toast._removed = true;
  clearTimeout(toast._autoRemove);
  toast.classList.add("removing");
  toast.addEventListener("animationend", () => toast.remove());
}

// ─── Status (now uses toasts) ───────────────────
function setStatus(message, isError = false) {
  dom.authStatus.textContent = message;
  dom.authStatus.classList.toggle("error", isError);
  if (message) {
    showToast(message, isError ? "error" : "success");
  }
}

// ─── Button Loading State ───────────────────────
function setButtonLoading(button, loading) {
  if (loading) {
    button.classList.add("btn-loading");
    button.disabled = true;
  } else {
    button.classList.remove("btn-loading");
    button.disabled = false;
  }
}

// ─── Session Management ─────────────────────────
function saveSession() {
  if (!state.user) {
    localStorage.removeItem(storageKey);
    return;
  }

  localStorage.setItem(storageKey, JSON.stringify({ token: state.token, user: state.user }));
}

function restoreSession() {
  const raw = localStorage.getItem(storageKey);
  if (!raw) {
    return;
  }

  try {
    const session = JSON.parse(raw);
    if (session && session.user) {
      state.token = session.token || null;
      state.user = session.user;
      syncUiForSession();
      loadNotes().catch((error) => setStatus(`Load failed: ${error.message}`, true));
    }
  } catch {
    localStorage.removeItem(storageKey);
  }
}

// ─── API Helper ─────────────────────────────────
async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "content-type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}

// ─── UI Sync ────────────────────────────────────
function syncUiForSession() {
  const loggedIn = Boolean(state.user);

  // Animated view transition
  if (loggedIn && !dom.authPanel.hidden) {
    dom.authPanel.classList.add("view-exit");
    setTimeout(() => {
      dom.authPanel.hidden = true;
      dom.authPanel.classList.remove("view-exit");
      dom.dashboard.hidden = false;
      dom.dashboard.classList.add("view-enter");
      setTimeout(() => dom.dashboard.classList.remove("view-enter"), 500);
    }, 280);
  } else if (!loggedIn && !dom.dashboard.hidden) {
    dom.dashboard.classList.add("view-exit");
    setTimeout(() => {
      dom.dashboard.hidden = true;
      dom.dashboard.classList.remove("view-exit");
      dom.authPanel.hidden = false;
      dom.authPanel.classList.add("view-enter");
      setTimeout(() => dom.authPanel.classList.remove("view-enter"), 500);
    }, 280);
  } else {
    dom.authPanel.hidden = loggedIn;
    dom.dashboard.hidden = !loggedIn;
  }

  dom.sessionBadge.textContent = loggedIn ? `${state.user.username}` : "Signed out";
  dom.sessionBadge.classList.toggle("online", loggedIn);
  dom.welcomeTitle.textContent = loggedIn ? `${state.user.username}'s notes` : "Your notes";
}

// ─── Note Count ─────────────────────────────────
function updateNoteCount() {
  const count = state.notes.length;
  dom.noteCountBadge.textContent = `${count} note${count !== 1 ? "s" : ""}`;

  const categoryNames = new Set([...state.noteCategories.values()].flat());
  dom.statTotal.textContent = String(count);
  dom.statPinned.textContent = String(state.notes.filter((noteItem) => noteItem.is_pinned).length);
  dom.statCategories.textContent = String(categoryNames.size);
}

// ─── Formatting ─────────────────────────────────
function formatTimestamp(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function splitCategories(input) {
  return input
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
}

function getVisibleNotes() {
  const notes = state.notes.filter((noteItem) => {
    if (state.pinFilter === "pinned" && !noteItem.is_pinned) return false;
    if (state.pinFilter === "unpinned" && noteItem.is_pinned) return false;
    if (state.categoryFilter) {
      const categories = state.noteCategories.get(noteItem.note_id) || [];
      return categories.includes(state.categoryFilter);
    }
    return true;
  });

  return notes.sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) return Number(b.is_pinned) - Number(a.is_pinned);
    if (state.sortMode === "title_asc") return a.title.localeCompare(b.title);
    if (state.sortMode === "created_desc") return new Date(b.created_date) - new Date(a.created_date);
    return new Date(b.modified_date) - new Date(a.modified_date);
  });
}

function renderCategoryFilters() {
  const categoryNames = [...new Set([...state.noteCategories.values()].flat())].sort((a, b) => a.localeCompare(b));
  dom.categoryFilters.innerHTML = "";

  if (!categoryNames.length) return;

  const allButton = document.createElement("button");
  allButton.type = "button";
  allButton.className = `filter-chip ${state.categoryFilter ? "" : "active"}`;
  allButton.textContent = "All tags";
  allButton.addEventListener("click", () => {
    state.categoryFilter = "";
    renderNotes();
  });
  dom.categoryFilters.appendChild(allButton);

  for (const categoryName of categoryNames) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `filter-chip ${state.categoryFilter === categoryName ? "active" : ""}`;
    button.textContent = categoryName;
    button.addEventListener("click", () => {
      state.categoryFilter = categoryName;
      renderNotes();
    });
    dom.categoryFilters.appendChild(button);
  }
}

// ─── Categories ─────────────────────────────────
async function assignCategories(noteId, categories) {
  for (const name of categories) {
    await requestJson(`${base}/categories`, {
      method: "POST",
      body: JSON.stringify({ note_id: noteId, name }),
    });
  }
}

// ─── Loading State ──────────────────────────────
function showSkeleton() {
  dom.notesSkeleton.hidden = false;
  dom.notesEmpty.hidden = true;
  dom.notesList.innerHTML = "";
}

function hideSkeleton() {
  dom.notesSkeleton.hidden = true;
}

// ─── Notes CRUD ─────────────────────────────────
async function loadNotes() {
  if (!state.user) {
    return;
  }

  showSkeleton();

  const query = encodeURIComponent(state.searchQuery);
  state.notes = await requestJson(`${base}/notes?user_id=${state.user.user_id}&q=${query}`, {
    method: "GET",
    headers: {},
  });

  hideSkeleton();
  await renderNotes();
}

async function renderNotes() {
  dom.notesList.innerHTML = "";

  state.noteCategories = new Map();
  await Promise.all(
    state.notes.map(async (noteItem) => {
      const categories = await requestJson(`${base}/categories?note_id=${noteItem.note_id}`, {
        method: "GET",
        headers: {},
      });
      state.noteCategories.set(noteItem.note_id, categories);
    })
  );
  renderCategoryFilters();
  updateNoteCount();

  const visibleNotes = getVisibleNotes();
  dom.notesEmpty.hidden = visibleNotes.length > 0;

  if (!visibleNotes.length) {
    const emptyTitle = dom.notesEmpty.querySelector(".empty-state-title");
    const emptyText = dom.notesEmpty.querySelector(".empty-state-text");
    emptyTitle.textContent = state.notes.length ? "No matching notes" : "No notes yet";
    emptyText.textContent = state.notes.length
      ? "Try a different search, tag, or pinned filter."
      : "Create your first securely encrypted note using the form.";
    return;
  }

  for (const noteItem of visibleNotes) {
    const fragment = dom.noteTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".note-card");
    const pinLabel = fragment.querySelector(".pin-label");
    const title = fragment.querySelector("h4");
    const meta = fragment.querySelector(".note-meta");
    const content = fragment.querySelector(".note-content");
    const tags = fragment.querySelector(".note-tags");
    const pinButton = fragment.querySelector(".note-pin-btn");
    const copyButton = fragment.querySelector(".note-copy-btn");
    const editButton = fragment.querySelector(".note-edit-btn");
    const deleteButton = fragment.querySelector(".note-delete-btn");

    card.dataset.color = noteItem.color || "violet";
    card.classList.toggle("pinned", Boolean(noteItem.is_pinned));
    pinLabel.hidden = !noteItem.is_pinned;
    title.textContent = noteItem.title;
    meta.textContent = `${noteItem.is_pinned ? "Pinned · " : ""}Updated ${formatTimestamp(noteItem.modified_date)}`;
    content.textContent = noteItem.content;

    const categoryList = state.noteCategories.get(noteItem.note_id) || [];
    tags.innerHTML = "";
    for (const categoryName of categoryList) {
      const badge = document.createElement("span");
      badge.className = "tag-badge";
      badge.textContent = categoryName;
      tags.appendChild(badge);
    }

    pinButton.title = noteItem.is_pinned ? "Unpin note" : "Pin note";
    pinButton.classList.toggle("active", Boolean(noteItem.is_pinned));
    pinButton.addEventListener("click", () => togglePin(noteItem));
    copyButton.addEventListener("click", () => copyNote(noteItem, categoryList));
    editButton.addEventListener("click", () => openEditDialog(noteItem, categoryList));
    deleteButton.addEventListener("click", () => openConfirmDialog(noteItem.note_id, noteItem.title));

    dom.notesList.appendChild(fragment);
  }
}

// ─── Edit Dialog ────────────────────────────────
function openEditDialog(noteItem, categories = []) {
  dom.editNoteId.value = String(noteItem.note_id);
  dom.editTitle.value = noteItem.title;
  dom.editContent.value = noteItem.content;
  dom.editCategories.value = categories.join(", ");
  dom.editColor.value = noteItem.color || "violet";
  dom.editPinned.checked = Boolean(noteItem.is_pinned);

  if (typeof dom.editDialog.showModal === "function") {
    dom.editDialog.showModal();
  } else {
    dom.editDialog.setAttribute("open", "open");
  }
}

function closeEditDialog() {
  if (typeof dom.editDialog.close === "function") {
    dom.editDialog.close();
  } else {
    dom.editDialog.removeAttribute("open");
  }
}

// ─── Custom Confirm Dialog ──────────────────────
function openConfirmDialog(noteId, title) {
  state.pendingDeleteId = noteId;
  state.pendingDeleteTitle = title;
  dom.confirmMessage.textContent = `Are you sure you want to delete "${title}"? This action cannot be undone.`;

  if (typeof dom.confirmDialog.showModal === "function") {
    dom.confirmDialog.showModal();
  } else {
    dom.confirmDialog.setAttribute("open", "open");
  }
}

function closeConfirmDialog() {
  state.pendingDeleteId = null;
  state.pendingDeleteTitle = "";
  if (typeof dom.confirmDialog.close === "function") {
    dom.confirmDialog.close();
  } else {
    dom.confirmDialog.removeAttribute("open");
  }
}

// ─── Note Operations ────────────────────────────
async function createNote() {
  if (!state.user) {
    setStatus("Please log in or register first.", true);
    return;
  }

  const title = dom.noteTitle.value.trim();
  const content = dom.noteContent.value.trim();
  const categories = splitCategories(dom.noteCategories.value);
  const color = dom.noteColor.value;
  const isPinned = dom.notePinned.checked;

  if (!title || !content) {
    setStatus("Title and content are required.", true);
    return;
  }

  const btn = document.getElementById("btn_create_note");
  setButtonLoading(btn, true);

  try {
    const data = await requestJson(`${base}/notes`, {
      method: "POST",
      body: JSON.stringify({
        user_id: state.user.user_id,
        title,
        content,
        color,
        is_pinned: isPinned,
      }),
    });

    if (categories.length) {
      await assignCategories(data.note_id, categories);
    }

    dom.noteForm.reset();
    dom.noteTitle.focus();
    setStatus("Note created successfully.");
    await loadNotes();
  } finally {
    setButtonLoading(btn, false);
  }
}

async function saveNoteEdits(event) {
  event.preventDefault();

  if (!state.user) {
    setStatus("Please log in or register first.", true);
    return;
  }

  const noteId = Number(dom.editNoteId.value);
  const title = dom.editTitle.value.trim();
  const content = dom.editContent.value.trim();
  const categories = splitCategories(dom.editCategories.value);
  const color = dom.editColor.value;
  const isPinned = dom.editPinned.checked;

  if (!title || !content) {
    setStatus("Title and content are required.", true);
    return;
  }

  const btn = document.getElementById("btn_save_edit");
  setButtonLoading(btn, true);

  try {
    await requestJson(`${base}/notes/${noteId}`, {
      method: "PUT",
      body: JSON.stringify({
        user_id: state.user.user_id,
        title,
        content,
        color,
        is_pinned: isPinned,
      }),
    });

    await requestJson(`${base}/categories/${noteId}`, {
      method: "PUT",
      body: JSON.stringify({ names: categories }),
    });

    closeEditDialog();
    setStatus("Note updated successfully.");
    await loadNotes();
  } finally {
    setButtonLoading(btn, false);
  }
}

async function deleteNote(noteId) {
  if (!state.user) {
    setStatus("Please log in or register first.", true);
    return;
  }

  const btn = dom.btnConfirmDelete;
  setButtonLoading(btn, true);

  try {
    await requestJson(`${base}/notes/${noteId}?user_id=${state.user.user_id}`, {
      method: "DELETE",
      headers: {},
    });

    closeConfirmDialog();
    setStatus("Note deleted successfully.");
    await loadNotes();
  } finally {
    setButtonLoading(btn, false);
  }
}

async function togglePin(noteItem) {
  try {
    await requestJson(`${base}/notes/${noteItem.note_id}`, {
      method: "PUT",
      body: JSON.stringify({
        user_id: state.user.user_id,
        is_pinned: !noteItem.is_pinned,
      }),
    });
    showToast(noteItem.is_pinned ? "Note unpinned." : "Note pinned.", "success");
    await loadNotes();
  } catch (error) {
    setStatus(`Pin failed: ${error.message}`, true);
  }
}

async function copyNote(noteItem, categories) {
  const tagLine = categories.length ? `\nTags: ${categories.join(", ")}` : "";
  const text = `${noteItem.title}\n\n${noteItem.content}${tagLine}`;

  try {
    await navigator.clipboard.writeText(text);
    showToast("Note copied to clipboard.", "success");
  } catch {
    showToast("Clipboard access is unavailable in this browser.", "error");
  }
}

// ─── Auth ───────────────────────────────────────
async function registerUser(event) {
  event.preventDefault();

  const username = document.getElementById("reg_username").value.trim();
  const email = document.getElementById("reg_email").value.trim();
  const password = document.getElementById("reg_password").value;

  const btn = document.getElementById("btn_register");
  setButtonLoading(btn, true);

  try {
    const data = await requestJson(`${base}/register`, {
      method: "POST",
      body: JSON.stringify({ username, email, password }),
    });
    dom.registerForm.reset();
    resetPasswordStrength();

    const loginData = await requestJson(`${base}/login`, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });

    state.token = loginData.token;
    state.user = loginData.user;
    state.searchQuery = "";
    state.categoryFilter = "";
    saveSession();
    syncUiForSession();
    dom.loginForm.reset();
    setStatus(`Registered and signed in as ${data.username}.`);
    await loadNotes();
  } catch (error) {
    setStatus(`Register failed: ${error.message}`, true);
  } finally {
    setButtonLoading(btn, false);
  }
}

async function loginUser(event) {
  event.preventDefault();

  const username = document.getElementById("login_username").value.trim();
  const password = document.getElementById("login_password").value;

  const btn = document.getElementById("btn_login");
  setButtonLoading(btn, true);

  try {
    const data = await requestJson(`${base}/login`, {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });

    state.token = data.token;
    state.user = data.user;
    state.searchQuery = "";
    state.categoryFilter = "";
    saveSession();
    syncUiForSession();
    dom.loginForm.reset();
    setStatus(`Welcome back, ${state.user.username}.`);
    await loadNotes();
  } catch (error) {
    setStatus(`Login failed: ${error.message}`, true);
  } finally {
    setButtonLoading(btn, false);
  }
}

async function logoutUser() {
  if (state.token) {
    try {
      await requestJson(`${base}/logout`, {
        method: "POST",
        body: JSON.stringify({ token: state.token }),
      });
    } catch {
      // If the token is already invalid, clear local state anyway.
    }
  }

  state.token = null;
  state.user = null;
  state.notes = [];
  state.noteCategories = new Map();
  state.searchQuery = "";
  state.categoryFilter = "";
  localStorage.removeItem(storageKey);
  syncUiForSession();
  dom.notesList.innerHTML = "";
  dom.categoryFilters.innerHTML = "";
  dom.notesEmpty.hidden = false;
  updateNoteCount();
  setStatus("Signed out.");
}

// ─── Search ─────────────────────────────────────
function searchNotes() {
  state.searchQuery = dom.searchInput.value.trim();
  loadNotes().catch((error) => setStatus(`Search failed: ${error.message}`, true));
}

// ─── Password Strength Meter ────────────────────
function evaluatePasswordStrength(password) {
  let score = 0;
  if (password.length >= 6) score++;
  if (password.length >= 10) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 1) return { strength: "weak", label: "Weak", count: 1 };
  if (score <= 2) return { strength: "fair", label: "Fair", count: 2 };
  if (score <= 3) return { strength: "good", label: "Good", count: 3 };
  return { strength: "strong", label: "Strong", count: 4 };
}

function updatePasswordStrength() {
  const password = dom.regPassword.value;
  if (!password) {
    resetPasswordStrength();
    return;
  }

  const { strength, label, count } = evaluatePasswordStrength(password);
  dom.strengthMeter.setAttribute("data-strength", strength);

  const bars = dom.strengthMeter.querySelectorAll(".strength-meter-bar");
  bars.forEach((bar, i) => {
    bar.classList.toggle("filled", i < count);
  });

  dom.strengthLabel.textContent = label;
}

function resetPasswordStrength() {
  dom.strengthMeter.setAttribute("data-strength", "");
  dom.strengthMeter.querySelectorAll(".strength-meter-bar").forEach((bar) => {
    bar.classList.remove("filled");
  });
  dom.strengthLabel.textContent = "";
}

// ─── Export / Import ────────────────────────────
async function exportNotes() {
  if (!state.user) {
    showToast("Please log in first.", "error");
    return;
  }

  try {
    showToast("Preparing export...", "info", 2000);
    const response = await fetch(`${base}/backup/export`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ user_id: state.user.user_id }),
    });

    if (!response.ok) {
      throw new Error("Export failed");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `guptrix-backup-${state.user.username}-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast("Notes exported successfully!", "success");
  } catch (error) {
    showToast(`Export failed: ${error.message}`, "error");
  }
}

async function importNotes(file) {
  if (!state.user) {
    showToast("Please log in first.", "error");
    return;
  }

  try {
    const text = await file.text();
    const payload = JSON.parse(text);

    showToast("Importing notes...", "info", 2000);

    const data = await requestJson(`${base}/backup/import`, {
      method: "POST",
      body: JSON.stringify({ user_id: state.user.user_id, payload }),
    });

    showToast(`Successfully imported ${data.imported} note(s)!`, "success");
    await loadNotes();
  } catch (error) {
    showToast(`Import failed: ${error.message}`, "error");
  }
}

// ─── Mobile Sidebar Toggle ──────────────────────
function openSidebar() {
  dom.sidebar.classList.add("sidebar-open");
  dom.sidebarOverlay.classList.add("visible");
  dom.sidebarOverlay.style.display = "block";
}

function closeSidebar() {
  dom.sidebar.classList.remove("sidebar-open");
  dom.sidebarOverlay.classList.remove("visible");
  setTimeout(() => {
    dom.sidebarOverlay.style.display = "none";
  }, 300);
}

// ─── Event Listeners ────────────────────────────

// Auth
dom.registerForm.addEventListener("submit", registerUser);
dom.loginForm.addEventListener("submit", loginUser);
dom.btnLogout.addEventListener("click", logoutUser);

// Notes
dom.noteForm.addEventListener("submit", (event) => {
  event.preventDefault();
  createNote().catch((error) => setStatus(`Create failed: ${error.message}`, true));
});
dom.editForm.addEventListener("submit", saveNoteEdits);
document.getElementById("btn_cancel_edit").addEventListener("click", closeEditDialog);

// Search
dom.btnSearch.addEventListener("click", searchNotes);
dom.btnClearSearch.addEventListener("click", () => {
  dom.searchInput.value = "";
  state.searchQuery = "";
  loadNotes().catch((error) => setStatus(`Search failed: ${error.message}`, true));
});
dom.searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    searchNotes();
  }
});
dom.sortNotes.addEventListener("change", () => {
  state.sortMode = dom.sortNotes.value;
  renderNotes();
});
dom.filterPin.addEventListener("change", () => {
  state.pinFilter = dom.filterPin.value;
  renderNotes();
});

// Confirm dialog
dom.btnConfirmCancel.addEventListener("click", closeConfirmDialog);
dom.btnConfirmDelete.addEventListener("click", () => {
  if (state.pendingDeleteId != null) {
    deleteNote(state.pendingDeleteId).catch((error) =>
      setStatus(`Delete failed: ${error.message}`, true)
    );
  }
});

// Password strength
dom.regPassword.addEventListener("input", updatePasswordStrength);

// Export / Import
dom.btnExport.addEventListener("click", exportNotes);
dom.btnExport.addEventListener("keydown", (e) => { if (e.key === "Enter") exportNotes(); });

dom.btnImport.addEventListener("click", () => dom.importFile.click());
dom.btnImport.addEventListener("keydown", (e) => { if (e.key === "Enter") dom.importFile.click(); });

dom.importFile.addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) {
    importNotes(file);
    event.target.value = "";
  }
});

// Sidebar nav items (export/import from sidebar)
dom.navNotes.addEventListener("click", () => {
  closeSidebar();
  document.querySelector(".content-scroll").scrollTo({ top: 0, behavior: "smooth" });
});

dom.navExport.addEventListener("click", () => {
  closeSidebar();
  if (state.user) {
    exportNotes();
  } else {
    showToast("Please log in first.", "error");
  }
});

dom.navImport.addEventListener("click", () => {
  closeSidebar();
  if (state.user) {
    dom.importFile.click();
  } else {
    showToast("Please log in first.", "error");
  }
});

dom.navShortcuts.addEventListener("click", () => {
  closeSidebar();
  showToast("Ctrl+N: New note · Ctrl+Shift+F: Search · Esc: Close", "info", 6000);
});

// Mobile sidebar
dom.hamburgerBtn.addEventListener("click", openSidebar);
dom.sidebarCloseBtn.addEventListener("click", closeSidebar);
dom.sidebarOverlay.addEventListener("click", closeSidebar);

// ─── Keyboard Shortcuts ─────────────────────────
document.addEventListener("keydown", (event) => {
  // Escape — close any open dialog
  if (event.key === "Escape") {
    if (dom.editDialog.open) {
      closeEditDialog();
    }
    if (dom.confirmDialog.open) {
      closeConfirmDialog();
    }
    closeSidebar();
  }

  // Ctrl+N — focus new note title
  if ((event.ctrlKey || event.metaKey) && event.key === "n") {
    if (state.user && !dom.dashboard.hidden) {
      event.preventDefault();
      dom.noteTitle.focus();
      dom.noteTitle.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  // Ctrl+Shift+F — focus search
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === "F") {
    if (state.user && !dom.dashboard.hidden) {
      event.preventDefault();
      dom.searchInput.focus();
    }
  }
});

// ─── Initialization ─────────────────────────────
restoreSession();
syncUiForSession();
