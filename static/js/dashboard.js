if (!requireAuth()) throw new Error("redirecting");

const $ = (s) => document.querySelector(s);

function setStatus(text, cls) {
  const el = $("#telegram-status");
  el.textContent = text;
  el.className = `telegram-status-badge ${cls}`;
}

async function updateTelegramUI() {
  const actions = $("#telegram-actions");
  const errorEl = $("#telegram-error");
  errorEl.textContent = "";

  let user, status;
  try {
    [user, status] = await Promise.all([
      apiFetch("/api/auth/me"),
      apiFetch("/api/telegram/status").catch(() => null),
    ]);
  } catch (e) {
    setStatus("Ошибка", "telegram-status-warn");
    return;
  }

  const connected = user.telegram_connected || status?.connected;

  if (!status?.configured && !connected) {
    setStatus("Бот не настроен", "telegram-status-warn");
    actions.classList.add("hidden");
    errorEl.textContent = "Добавьте TELEGRAM_BOT_TOKEN в .env на сервере.";
    return;
  }

  actions.classList.remove("hidden");

  if (connected) {
    const bot = status?.bot_username ? `@${status.bot_username}` : "Telegram";
    setStatus(`Подключено (${bot})`, "telegram-status-ok");
    $("#telegram-link").textContent = "Переподключить";
    $("#btn-telegram-disconnect").classList.remove("hidden");
  } else {
    setStatus("Не подключено", "telegram-status-off");
    $("#telegram-link").textContent = "Подключить Telegram";
    $("#btn-telegram-disconnect").classList.add("hidden");
  }

  $("#telegram-link").onclick = async (e) => {
    e.preventDefault();
    try {
      const res = await apiFetch("/api/telegram/link", { method: "POST" });
      window.open(res.link, "_blank");
      $("#telegram-success").textContent = "Нажмите Start в Telegram";
      pollTelegram();
    } catch (err) {
      errorEl.textContent = err.message;
    }
  };
}

function pollTelegram() {
  let n = 0;
  const t = setInterval(async () => {
    n++;
    const u = await apiFetch("/api/auth/me");
    if (u.telegram_connected) {
      clearInterval(t);
      updateTelegramUI();
      $("#telegram-success").textContent = "Telegram подключён!";
    } else if (n > 30) clearInterval(t);
  }, 2000);
}

async function init() {
  const [user, stats] = await Promise.all([
    apiFetch("/api/auth/me"),
    apiFetch("/api/auth/me/stats"),
  ]);

  $("#user-name").textContent = user.name;
  $("#user-email").textContent = user.email;
  $("#profile-avatar").textContent = user.name.charAt(0).toUpperCase();
  $("#user-created").textContent = new Date(user.created_at).toLocaleDateString("ru-RU", {
    day: "numeric", month: "long", year: "numeric",
  });
  $("#stat-events").textContent = stats.events_count;
  $("#stat-active").textContent = stats.active_events;
  $("#form-name").value = user.name;

  await updateTelegramUI();
}

$("#btn-telegram-refresh").onclick = () => updateTelegramUI();
$("#btn-telegram-disconnect").onclick = async () => {
  if (!confirm("Отключить Telegram?")) return;
  await apiFetch("/api/telegram/disconnect", { method: "DELETE" });
  updateTelegramUI();
};

$("#profile-form").onsubmit = async (e) => {
  e.preventDefault();
  const updates = { name: $("#form-name").value.trim() };
  if ($("#form-password").value) updates.password = $("#form-password").value;
  try {
    const u = await apiFetch("/api/auth/me", { method: "PATCH", body: JSON.stringify(updates) });
    $("#user-name").textContent = u.name;
    $("#form-password").value = "";
    $("#profile-success").textContent = "Сохранено";
  } catch (err) {
    $("#profile-error").textContent = err.message;
  }
};

$("#btn-logout").onclick = logout;
init();
