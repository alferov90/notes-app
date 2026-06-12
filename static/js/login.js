if (redirectIfAuthed()) throw new Error("redirecting");

const form = document.getElementById("login-form");
const errorEl = document.getElementById("form-error");
const submitBtn = document.getElementById("submit-btn");

function getNextUrl() {
  const params = new URLSearchParams(window.location.search);
  const next = params.get("next");
  return next && next.startsWith("/") ? next : "/app";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.textContent = "";
  submitBtn.disabled = true;
  submitBtn.textContent = "Вход…";

  try {
    const data = {
      email: form.email.value.trim(),
      password: form.password.value,
    };
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    setToken(res.access_token);
    window.location.href = getNextUrl();
  } catch (err) {
    errorEl.textContent = err.message;
    submitBtn.disabled = false;
    submitBtn.textContent = "Войти";
  }
});
