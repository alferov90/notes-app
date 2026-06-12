const THEME_KEY = "noteflow_theme";

function getTheme() {
  return localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark";
}

function applyTheme(theme) {
  if (theme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

function setTheme(theme) {
  localStorage.setItem(THEME_KEY, theme);
  applyTheme(theme);
  syncThemeToggle();
}

function syncThemeToggle() {
  const toggle = document.getElementById("theme-toggle");
  if (toggle) toggle.checked = getTheme() === "light";
}

function initThemeToggle() {
  applyTheme(getTheme());
  syncThemeToggle();
  const toggle = document.getElementById("theme-toggle");
  if (!toggle) return;
  toggle.addEventListener("change", () => {
    setTheme(toggle.checked ? "light" : "dark");
  });
}
