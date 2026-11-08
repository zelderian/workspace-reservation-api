const TOKEN_KEY = "wr_token";

function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
function setToken(token) {
  try { localStorage.setItem(TOKEN_KEY, token); } catch {}
}
function logout() {
  try { localStorage.removeItem(TOKEN_KEY); } catch {}
  location.href = "/login.html";
}

function errorText(data, status) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) return data.detail.map((e) => e.msg).join("; ");
  return `Помилка ${status}`;
}

async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = new URLSearchParams(form);
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const resp = await fetch(path, { method, headers, body: payload });
  const data = await resp.json().catch(() => null);
  if (resp.status === 401 && token) { logout(); }
  if (!resp.ok) throw new Error(errorText(data, resp.status));
  return data;
}

async function requireUser() {
  if (!getToken()) { location.href = "/login.html"; return null; }
  return api("/users/me");
}

function showMsg(el, text, ok = false) {
  el.textContent = text;
  el.className = "msg " + (ok ? "ok" : "error");
}

function fmtDate(iso) {
  const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
  return d.toLocaleString("uk-UA", { dateStyle: "medium", timeStyle: "short" });
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

const TYPES = { desk: "Робоче місце", meeting_room: "Переговорна", hall: "Конференц-зал" };
function typeName(t) { return TYPES[t] || t; }
