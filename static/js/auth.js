const TOKEN_KEY = "noteflow_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function requireAuth(redirectTo = "/login") {
  if (!getToken()) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `${redirectTo}?next=${next}`;
    return false;
  }
  return true;
}

function redirectIfAuthed(target = "/app") {
  if (getToken()) {
    window.location.href = target;
    return true;
  }
  return false;
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail.map((e) => e.msg).join(", ")
      : detail || `HTTP ${res.status}`;
    throw new Error(message);
  }
  return data;
}

function logout() {
  clearToken();
  window.location.href = "/";
}
