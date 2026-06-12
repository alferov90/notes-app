if (redirectIfAuthed()) throw new Error("redirecting");

const form = document.getElementById("register-form");
const errorEl = document.getElementById("form-error");
const submitBtn = document.getElementById("submit-btn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.textContent = "";

  if (form.password.value !== form.password_confirm.value) {
    errorEl.textContent = "Пароли не совпадают";
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Создание…";

  try {
    const data = {
      name: form.name.value.trim(),
      email: form.email.value.trim(),
      password: form.password.value,
    };
    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    setToken(res.access_token);
    window.location.href = "/app";
  } catch (err) {
    errorEl.textContent = err.message;
    submitBtn.disabled = false;
    submitBtn.textContent = "Создать аккаунт";
  }
});
