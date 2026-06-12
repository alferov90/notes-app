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

  $("#form-name").value = user.name;
}

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
