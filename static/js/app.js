if (!requireAuth()) throw new Error("redirecting");

const API = "/api/notes";

let notes = [];
let activeId = null;
let saveTimer = null;
let isSaving = false;
let currentUser = null;

const $ = (sel) => document.querySelector(sel);

const notesList = $("#notes-list");
const searchInput = $("#search");
const emptyState = $("#empty-state");
const editorContent = $("#editor-content");
const noteTitle = $("#note-title");
const noteContent = $("#note-content");
const noteMeta = $("#note-meta");
const saveStatus = $("#save-status");
const btnNew = $("#btn-new");
const btnPin = $("#btn-pin");
const btnDelete = $("#btn-delete");
const colorPicker = $("#color-picker");
const userName = $("#user-name");
const userEmail = $("#user-email");

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function preview(text, max = 80) {
  const line = text.replace(/\n/g, " ").trim();
  return line.length > max ? line.slice(0, max) + "…" : line || "Без содержимого";
}

async function api(path = "", options = {}) {
  return apiFetch(`${API}${path}`, options);
}

function getActiveNote() {
  return notes.find((n) => n.id === activeId) ?? null;
}

function renderList() {
  notesList.innerHTML = "";

  if (notes.length === 0) {
    notesList.innerHTML = '<li class="list-empty">Заметок пока нет</li>';
    return;
  }

  for (const note of notes) {
    const li = document.createElement("li");
    li.className = "note-item" + (note.id === activeId ? " active" : "");
    li.dataset.id = note.id;
    li.innerHTML = `
      <div class="note-item-color" style="--note-color:${note.color}"></div>
      <div class="note-item-body">
        <div class="note-item-title">${escapeHtml(note.title || "Без названия")}</div>
        <div class="note-item-preview">${escapeHtml(preview(note.content))}</div>
        <div class="note-item-meta">
          ${note.is_pinned ? '<span class="pin-icon" title="Закреплено">📌</span>' : ""}
          <span>${formatDate(note.updated_at)}</span>
        </div>
      </div>
    `;
    li.addEventListener("click", () => selectNote(note.id));
    notesList.appendChild(li);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showEditor(show) {
  emptyState.classList.toggle("hidden", show);
  editorContent.classList.toggle("hidden", !show);
}

function updateToolbar(note) {
  btnPin.classList.toggle("active", note.is_pinned);
  colorPicker.querySelectorAll(".color-dot").forEach((dot) => {
    dot.classList.toggle("active", dot.dataset.color === note.color);
  });
  noteMeta.textContent = `Создано: ${formatDate(note.created_at)} · Изменено: ${formatDate(note.updated_at)}`;
}

function selectNote(id) {
  activeId = id;
  const note = getActiveNote();
  if (!note) return;

  showEditor(true);
  noteTitle.value = note.title;
  noteContent.value = note.content;
  updateToolbar(note);
  renderList();
}

async function loadNotes(search = "") {
  const q = search ? `?search=${encodeURIComponent(search)}` : "";
  notes = await api(q);
  renderList();

  if (activeId && !notes.find((n) => n.id === activeId)) {
    activeId = notes.length ? notes[0].id : null;
  }

  if (activeId) {
    selectNote(activeId);
  } else {
    showEditor(false);
  }
}

async function createNote() {
  const note = await api("", {
    method: "POST",
    body: JSON.stringify({ title: "Новая заметка", content: "", color: "#6366f1" }),
  });
  notes.unshift(note);
  selectNote(note.id);
  noteTitle.focus();
  noteTitle.select();
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveNote, 500);
}

async function saveNote() {
  if (!activeId || isSaving) return;
  const note = getActiveNote();
  if (!note) return;

  isSaving = true;
  saveStatus.textContent = "Сохранение…";
  saveStatus.classList.add("visible");

  try {
    const updated = await api(`/${activeId}`, {
      method: "PATCH",
      body: JSON.stringify({
        title: noteTitle.value,
        content: noteContent.value,
        color: note.color,
        is_pinned: note.is_pinned,
      }),
    });

    const idx = notes.findIndex((n) => n.id === activeId);
    if (idx !== -1) notes[idx] = updated;
    updateToolbar(updated);
    renderList();

    saveStatus.textContent = "Сохранено";
    setTimeout(() => saveStatus.classList.remove("visible"), 1500);
  } catch (e) {
    saveStatus.textContent = "Ошибка сохранения";
    console.error(e);
  } finally {
    isSaving = false;
  }
}

async function togglePin() {
  const note = getActiveNote();
  if (!note) return;
  note.is_pinned = !note.is_pinned;
  await saveNote();
  notes.sort((a, b) => {
    if (a.is_pinned !== b.is_pinned) return b.is_pinned - a.is_pinned;
    return new Date(b.updated_at) - new Date(a.updated_at);
  });
  renderList();
}

async function deleteNote() {
  if (!activeId) return;
  if (!confirm("Удалить эту заметку?")) return;

  await api(`/${activeId}`, { method: "DELETE" });
  notes = notes.filter((n) => n.id !== activeId);
  activeId = notes.length ? notes[0].id : null;

  if (activeId) {
    selectNote(activeId);
  } else {
    showEditor(false);
    renderList();
  }
}

async function setColor(color) {
  const note = getActiveNote();
  if (!note) return;
  note.color = color;
  updateToolbar(note);
  await saveNote();
}

async function initUser() {
  currentUser = await apiFetch("/api/auth/me");
  userName.textContent = currentUser.name;
  userEmail.textContent = currentUser.email;
  const initial = currentUser.name.charAt(0).toUpperCase() || "?";
  $("#user-avatar").textContent = initial;
}

let searchTimer = null;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadNotes(searchInput.value), 300);
});

btnNew.addEventListener("click", createNote);
btnPin.addEventListener("click", togglePin);
btnDelete.addEventListener("click", deleteNote);
$("#btn-logout")?.addEventListener("click", logout);

noteTitle.addEventListener("input", scheduleSave);
noteContent.addEventListener("input", scheduleSave);

colorPicker.addEventListener("click", (e) => {
  const dot = e.target.closest(".color-dot");
  if (dot) setColor(dot.dataset.color);
});

Promise.all([initUser(), loadNotes()]).catch((e) => {
  notesList.innerHTML = `<li class="list-empty">Не удалось загрузить: ${e.message}</li>`;
});
