if (!requireAuth()) throw new Error("redirecting");

const $ = (sel) => document.querySelector(sel);

async function init() {
  const [user, stats] = await Promise.all([
    apiFetch("/api/auth/me"),
    apiFetch("/api/auth/me/stats"),
  ]);

  $("#user-name").textContent = user.name;
  $("#user-email").textContent = user.email;
  $("#profile-avatar").textContent = user.name.charAt(0).toUpperCase() || "?";
  $("#user-created").textContent = new Date(user.created_at).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  $("#stat-notes").textContent = stats.notes_count;
  $("#stat-pinned").textContent = stats.pinned_count;
  $("#stat-reminders").textContent = stats.reminders_count;

  $("#form-name").value = user.name;
  await updateTelegramUI();
}

async function updateTelegramUI() {
  const statusEl = $("#telegram-status");
  const actionsEl = $("#telegram-actions");
  const linkEl = $("#telegram-link");
  const disconnectBtn = $("#btn-telegram-disconnect");
  const errorEl = $("#telegram-error");

  errorEl.textContent = "";

  try {
    const status = await apiFetch("/api/telegram/status");

    if (!status.configured) {
      statusEl.textContent = "Бот не настроен на сервере";
      statusEl.className = "telegram-status-badge telegram-status-warn";
      actionsEl.classList.add("hidden");
      errorEl.textContent =
        "Администратор должен добавить TELEGRAM_BOT_TOKEN и TELEGRAM_BOT_USERNAME в .env на сервере.";
      return;
    }

    if (!status.bot_ok) {
      statusEl.textContent = "Ошибка бота";
      statusEl.className = "telegram-status-badge telegram-status-warn";
      actionsEl.classList.add("hidden");
      errorEl.textContent = status.bot_error || "Неверный токен бота";
      return;
    }

    actionsEl.classList.remove("hidden");

    if (status.connected) {
      statusEl.textContent = `Подключено (@${status.bot_username})`;
      statusEl.className = "telegram-status-badge telegram-status-ok";
      linkEl.textContent = "Переподключить";
      disconnectBtn.classList.remove("hidden");
    } else {
      statusEl.textContent = "Не подключено";
      statusEl.className = "telegram-status-badge telegram-status-off";
      linkEl.textContent = "Подключить Telegram";
      disconnectBtn.classList.add("hidden");
    }

    linkEl.onclick = async (e) => {
      e.preventDefault();
      errorEl.textContent = "";
      try {
        const res = await apiFetch("/api/telegram/link", { method: "POST" });
        window.open(res.link, "_blank", "noopener");
        $("#telegram-success").textContent =
          "В Telegram нажмите Start. Статус обновится автоматически…";
        startTelegramPoll();
      } catch (err) {
        errorEl.textContent = err.message;
      }
    };
  } catch (err) {
    statusEl.textContent = "Ошибка загрузки";
    statusEl.className = "telegram-status-badge telegram-status-warn";
    errorEl.textContent = err.message;
  }
}

let telegramPollTimer = null;

function startTelegramPoll() {
  clearInterval(telegramPollTimer);
  let attempts = 0;
  telegramPollTimer = setInterval(async () => {
    attempts++;
    const status = await apiFetch("/api/telegram/status");
    if (status.connected) {
      clearInterval(telegramPollTimer);
      await updateTelegramUI();
      $("#telegram-success").textContent = "Telegram успешно подключён!";
      setTimeout(() => ($("#telegram-success").textContent = ""), 4000);
    } else if (attempts >= 30) {
      clearInterval(telegramPollTimer);
      $("#telegram-error").textContent =
        "Не удалось подключить. Нажмите Start в боте и попробуйте снова.";
    }
  }, 2000);
}

$("#btn-telegram-refresh")?.addEventListener("click", async () => {
  await updateTelegramUI();
  $("#telegram-success").textContent = "Статус обновлён";
  setTimeout(() => ($("#telegram-success").textContent = ""), 2000);
});

$("#btn-telegram-disconnect")?.addEventListener("click", async () => {
  if (!confirm("Отключить Telegram-уведомления?")) return;
  try {
    await apiFetch("/api/telegram/disconnect", { method: "DELETE" });
    await updateTelegramUI();
    $("#telegram-success").textContent = "Telegram отключён";
    setTimeout(() => ($("#telegram-success").textContent = ""), 3000);
  } catch (err) {
    $("#telegram-error").textContent = err.message;
  }
});

$("#profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = $("#profile-error");
  const successEl = $("#profile-success");
  const btn = $("#save-profile");

  errorEl.textContent = "";
  successEl.textContent = "";
  btn.disabled = true;

  try {
    const updates = { name: $("#form-name").value.trim() };
    const password = $("#form-password").value;
    if (password) updates.password = password;

    const user = await apiFetch("/api/auth/me", {
      method: "PATCH",
      body: JSON.stringify(updates),
    });

    $("#user-name").textContent = user.name;
    $("#form-password").value = "";
    successEl.textContent = "Профиль обновлён";
    setTimeout(() => (successEl.textContent = ""), 3000);
  } catch (err) {
    errorEl.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#btn-logout")?.addEventListener("click", logout);

init().catch((e) => {
  $("#profile-error").textContent = e.message;
});
