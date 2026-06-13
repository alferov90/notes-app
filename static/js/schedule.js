if (!requireAuth()) throw new Error("redirecting");

const API = "/api/events";
const EMOJIS = ["⏰", "☀️", "🍳", "💼", "🏃", "🍽️", "📚", "💊", "🧘", "🚿", "😴", "☕"];
const DAYS = [
  { id: "0", label: "Пн" },
  { id: "1", label: "Вт" },
  { id: "2", label: "Ср" },
  { id: "3", label: "Чт" },
  { id: "4", label: "Пт" },
  { id: "5", label: "Сб" },
  { id: "6", label: "Вс" },
];

let events = [];
let editingId = null;
let selectedEmoji = "⏰";
let selectedDays = "all";

const $ = (s) => document.querySelector(s);

function formatDays(days) {
  if (days === "all") return "Каждый день";
  const map = Object.fromEntries(DAYS.map((d) => [d.id, d.label]));
  return days.split(",").map((d) => map[d.trim()] || d).join(", ");
}

function renderEmojiPicker() {
  const picker = $("#emoji-picker");
  picker.innerHTML = EMOJIS.map(
    (e) => `<button type="button" class="emoji-btn${e === selectedEmoji ? " active" : ""}" data-emoji="${e}">${e}</button>`
  ).join("");
  picker.onclick = (ev) => {
    const btn = ev.target.closest(".emoji-btn");
    if (!btn) return;
    selectedEmoji = btn.dataset.emoji;
    renderEmojiPicker();
  };
}

function renderDayChips() {
  const allActive = selectedDays === "all";
  const chips = $("#day-chips");
  chips.innerHTML =
    `<button type="button" class="day-chip${allActive ? " active" : ""}" data-day="all">Каждый день</button>` +
    DAYS.map(
      (d) => {
        const active = !allActive && selectedDays.split(",").includes(d.id);
        return `<button type="button" class="day-chip${active ? " active" : ""}" data-day="${d.id}">${d.label}</button>`;
      }
    ).join("");

  chips.onclick = (ev) => {
    const chip = ev.target.closest(".day-chip");
    if (!chip) return;
    if (chip.dataset.day === "all") {
      selectedDays = "all";
    } else {
      let set = selectedDays === "all" ? new Set() : new Set(selectedDays.split(",").filter(Boolean));
      const id = chip.dataset.day;
      if (set.has(id)) set.delete(id);
      else set.add(id);
      selectedDays = set.size === 7 ? "all" : [...set].sort().join(",");
      if (!selectedDays) selectedDays = "all";
    }
    renderDayChips();
  };
}

function renderTimeline() {
  const el = $("#timeline");
  if (!events.length) {
    el.innerHTML = `
      <div class="timeline-empty">
        <h2>Расписание пусто</h2>
        <p>Нажмите + и добавьте первое событие режима дня</p>
      </div>`;
    return;
  }

  el.innerHTML = events.map((ev) => `
    <div class="event-card${ev.is_active ? "" : " inactive"}" data-id="${ev.id}">
      <span class="event-time">${ev.event_time}</span>
      <span class="event-emoji">${ev.emoji}</span>
      <div class="event-body">
        <div class="event-title">${escapeHtml(ev.title)}</div>
        <div class="event-days">${formatDays(ev.days)}</div>
      </div>
      <div class="event-actions">
        <button class="btn btn-icon btn-edit" title="Изменить">✎</button>
        <button class="btn btn-icon btn-delete" title="Удалить">🗑</button>
      </div>
    </div>
  `).join("");

  el.querySelectorAll(".btn-edit").forEach((btn) => {
    btn.onclick = () => openEdit(+btn.closest(".event-card").dataset.id);
  });
  el.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.onclick = () => deleteEvent(+btn.closest(".event-card").dataset.id);
  });
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

function openModal() {
  $("#modal").classList.remove("hidden");
}

function closeModal() {
  $("#modal").classList.add("hidden");
  editingId = null;
  $("#form-error").textContent = "";
}

function openCreate() {
  editingId = null;
  $("#modal-title").textContent = "Новое событие";
  $("#event-title").value = "";
  $("#event-time").value = "08:00";
  selectedEmoji = "⏰";
  selectedDays = "all";
  renderEmojiPicker();
  renderDayChips();
  openModal();
}

function openEdit(id) {
  const ev = events.find((e) => e.id === id);
  if (!ev) return;
  editingId = id;
  $("#modal-title").textContent = "Изменить событие";
  $("#event-title").value = ev.title;
  $("#event-time").value = ev.event_time;
  selectedEmoji = ev.emoji;
  selectedDays = ev.days;
  renderEmojiPicker();
  renderDayChips();
  openModal();
}

async function loadEvents() {
  events = await apiFetch(API);
  renderTimeline();
}

async function deleteEvent(id) {
  if (!confirm("Удалить это событие?")) return;
  await apiFetch(`${API}/${id}`, { method: "DELETE" });
  events = events.filter((e) => e.id !== id);
  renderTimeline();
}

$("#event-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const err = $("#form-error");
  err.textContent = "";
  const body = {
    title: $("#event-title").value.trim(),
    event_time: $("#event-time").value + ":00",
    emoji: selectedEmoji,
    days: selectedDays,
    is_active: true,
  };
  try {
    if (editingId) {
      const updated = await apiFetch(`${API}/${editingId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      const idx = events.findIndex((e) => e.id === editingId);
      if (idx >= 0) events[idx] = updated;
    } else {
      const created = await apiFetch(API, { method: "POST", body: JSON.stringify(body) });
      events.push(created);
      events.sort((a, b) => a.event_time.localeCompare(b.event_time));
    }
    renderTimeline();
    closeModal();
  } catch (ex) {
    err.textContent = ex.message;
  }
});

$("#fab-add").onclick = openCreate;
$("#btn-cancel").onclick = closeModal;
$("#modal").onclick = (e) => { if (e.target === $("#modal")) closeModal(); };
$("#btn-logout").onclick = logout;

async function init() {
  const user = await apiFetch("/api/auth/me");
  $("#user-nav").textContent = user.name;

  const tg = await apiFetch("/api/telegram/status");
  if (!tg.connected) $("#telegram-banner").classList.remove("hidden");

  $("#today-date").textContent = new Date().toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  renderEmojiPicker();
  renderDayChips();
  await loadEvents();
}

init().catch((e) => {
  $("#timeline").innerHTML = `<div class="timeline-empty"><p>Ошибка: ${e.message}</p></div>`;
});
