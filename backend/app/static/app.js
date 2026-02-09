/* Minimal JS client for the MVP UI. */

function $(sel) { return document.querySelector(sel); }
function $all(sel) { return Array.from(document.querySelectorAll(sel)); }

function noticeEl() { return document.querySelector("[data-notice]"); }
function setNotice(message, type = "info") {
  const el = noticeEl();
  if (!el) return;
  el.textContent = message;
  el.dataset.type = type;
  el.hidden = false;
}
function clearNotice() {
  const el = noticeEl();
  if (!el) return;
  el.textContent = "";
  el.hidden = true;
  el.removeAttribute("data-type");
}

const api = {
  token() { return localStorage.getItem("token") || ""; },
  setToken(t) { localStorage.setItem("token", t); },
  clearToken() { localStorage.removeItem("token"); },
  headers() {
    const h = { "Content-Type": "application/json" };
    const t = api.token();
    if (t) h["Authorization"] = `Bearer ${t}`;
    return h;
  },
  async post(path, body) {
    const res = await fetch(`/api${path}`, { method: "POST", headers: api.headers(), body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  },
  async get(path) {
    const res = await fetch(`/api${path}`, { method: "GET", headers: api.headers() });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, data };
    return data;
  },
};

function applyAuthVisibility() {
  const authed = Boolean(api.token());
  $all("[data-auth]").forEach((el) => {
    const mode = el.getAttribute("data-auth");
    if (mode === "auth") el.style.display = authed ? "" : "none";
    if (mode === "guest") el.style.display = authed ? "none" : "";
  });
}

function bindLogout() {
  const btn = document.querySelector('[data-action="logout"]');
  if (!btn) return;
  btn.addEventListener("click", () => {
    api.clearToken();
    applyAuthVisibility();
    setNotice("Вы вышли из аккаунта.", "warn");
  });
}

async function loadTasks() {
  const list = document.querySelector("[data-tasks]");
  if (!list) return;
  const tasks = await api.get("/tasks?limit=50");

  list.innerHTML = "";
  for (const t of tasks) {
    const div = document.createElement("div");
    div.className = "taskItem";
    div.innerHTML = `
      <div class="taskItem__title"><a href="/ui/tasks/${t.id}">${t.title}</a></div>
      <div class="taskItem__meta">${t.subject} • ${t.topic} • сложность ${t.difficulty} • тип ${t.answer_type}</div>
    `;
    list.appendChild(div);
  }
}

async function loadAnalytics() {
  const box = document.querySelector("[data-analytics]");
  if (!box) return;
  try {
    const s = await api.get("/analytics/me/summary");
    box.innerHTML = `
      <div class="stats__row"><span>Всего отправок</span><strong>${s.total_submissions}</strong></div>
      <div class="stats__row"><span>Верных</span><strong>${s.correct_submissions}</strong></div>
      <div class="stats__row"><span>Точность</span><strong>${(s.accuracy * 100).toFixed(1)}%</strong></div>
    `;
  } catch (e) {
    box.innerHTML = `<p class="muted">Нужно войти, чтобы видеть аналитику.</p>`;
  }
}

function bindHomeActions() {
  $all("[data-action]").forEach((el) => {
    const act = el.getAttribute("data-action");
    if (act === "load-tasks") el.addEventListener("click", () => loadTasks().catch(() => setNotice("Ошибка загрузки задач", "error")));
    if (act === "load-analytics") el.addEventListener("click", () => loadAnalytics().catch(() => setNotice("Ошибка загрузки аналитики", "error")));
  });
}

function bindLoginForm() {
  const form = document.querySelector('[data-form="login"]');
  if (!form) return;
  if (api.token()) {
    window.location.href = "/ui";
    return;
  }
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearNotice();
    const fd = new FormData(form);
    const username = String(fd.get("username") || "");
    const password = String(fd.get("password") || "");

    const res = await fetch("/api/auth/token", {
      method: "POST",
      body: new URLSearchParams({ username, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { setNotice(data.detail || "Ошибка входа", "error"); return; }
    api.setToken(data.access_token);
    applyAuthVisibility();
    window.location.href = "/ui";
  });
}

function bindRegisterForm() {
  const form = document.querySelector('[data-form="register"]');
  if (!form) return;
  if (api.token()) {
    window.location.href = "/ui";
    return;
  }
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearNotice();
    const fd = new FormData(form);
    const payload = {
      email: String(fd.get("email") || ""),
      username: String(fd.get("username") || ""),
      password: String(fd.get("password") || ""),
    };
    try {
      await api.post("/auth/register", payload);
      setNotice("Аккаунт создан. Войдите.", "success");
      window.location.href = "/ui/login";
    } catch (err) {
      setNotice(err?.data?.detail || "Ошибка регистрации", "error");
    }
  });
}

async function loadTaskDetail() {
  const el = document.querySelector("[data-task]");
  if (!el) return;
  const taskId = el.getAttribute("data-task-id");
  let t;
  try {
    t = await api.get(`/tasks/${taskId}`);
  } catch (err) {
    setNotice(err?.data?.detail || "Не удалось загрузить задачу", "error");
    return;
  }
  el.innerHTML = `
    <div class="task__meta muted">${t.subject} • ${t.topic} • сложность ${t.difficulty} • тип ${t.answer_type}</div>
    <h2>${t.title}</h2>
    <div class="task__statement">${t.statement}</div>
    ${t.hints && t.hints.length ? `<div class="muted">Подсказки: ${t.hints.join(" • ")}</div>` : ""}
  `;
}

function bindSubmitAnswer() {
  const form = document.querySelector('[data-form="submit-answer"]');
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearNotice();
    if (!api.token()) {
      setNotice("Нужно войти, чтобы отправлять ответы.", "error");
      window.location.href = "/ui/login";
      return;
    }
    const fd = new FormData(form);
    const taskId = form.getAttribute("data-task-id");
    const answer = String(fd.get("answer") || "");
    try {
      const sub = await api.post(`/tasks/${taskId}/submit`, { answer });
      const ok = sub.is_correct === true;
      setNotice(ok ? "Ответ верный." : "Ответ неверный.", ok ? "success" : "error");
      const input = form.querySelector('input[name="answer"]');
      const btn = form.querySelector('button[type="submit"]');
      if (input) input.disabled = true;
      if (btn) btn.disabled = true;
    } catch (err) {
      if (err?.status === 409) {
        setNotice("Ответ уже отправлен.", "warn");
        const input = form.querySelector('input[name="answer"]');
        const btn = form.querySelector('button[type="submit"]');
        if (input) input.disabled = true;
        if (btn) btn.disabled = true;
        return;
      }
      if (err?.status === 401) {
        setNotice("Нужно войти, чтобы отправлять ответы.", "error");
        window.location.href = "/ui/login";
        return;
      }
      setNotice(err?.data?.detail || "Ошибка отправки ответа", "error");
    }
  });
}

function bindPvp() {
  const statusEl = document.querySelector("[data-pvp-status]");
  const matchEl = document.querySelector("[data-pvp-match]");
  const roundEl = document.querySelector("[data-pvp-round]");
  const taskEl = document.querySelector("[data-pvp-task]");
  const scoreEl = document.querySelector("[data-pvp-score]");
  const joinBtn = document.querySelector('[data-action="pvp-join"]');
  const leaveBtn = document.querySelector('[data-action="pvp-leave"]');
  const form = document.querySelector('[data-form="pvp-answer"]');

  if (!statusEl || !matchEl || !roundEl || !taskEl || !scoreEl || !joinBtn || !leaveBtn || !form) return;

  let ws = null;
  let matchId = null;
  let currentTaskId = null;
  let roundActive = false;
  let player1Score = 0;
  let player2Score = 0;

  function setStatus(t) { statusEl.textContent = t; }
  function setRound(r) { roundEl.textContent = `Раунд: ${r}`; }
  function setScore(a, b) { scoreEl.textContent = `Счет: ${a} - ${b}`; }

  function renderTask(t) {
    taskEl.innerHTML = `
      <div class="muted">${t.subject} • ${t.topic} • сложность ${t.difficulty}</div>
      <h2>${t.title}</h2>
      <div class="task__statement">${t.statement}</div>
    `;
  }

  function setRoundActive(active) {
    roundActive = active;
    const input = form.querySelector('input[name="answer"]');
    const btn = form.querySelector('button[type="submit"]');
    if (input) input.disabled = !active;
    if (btn) btn.disabled = !active;
  }

  function ensureWs() {
    const token = api.token();
    if (!token) { setNotice("Нужно войти, чтобы играть.", "error"); window.location.href = "/ui/login"; return null; }
    if (ws && ws.readyState === WebSocket.OPEN) return ws;
    ws = new WebSocket(`${location.origin.replace("http", "ws")}/api/pvp/ws?token=${encodeURIComponent(token)}`);
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "connected") setStatus("Подключено");
      if (msg.type === "queue_joined") setStatus("В очереди");
      if (msg.type === "queue_left") setStatus("Не в очереди");
      if (msg.type === "match_found") {
        matchId = msg.match_id;
        currentTaskId = msg.task.id;
        player1Score = 0;
        player2Score = 0;
        setStatus("Матч найден");
        matchEl.textContent = `Матч ${matchId}, соперник #${msg.opponent_user_id}`;
        setRound(msg.round || 1);
        renderTask(msg.task);
        setScore(player1Score, player2Score);
        setRoundActive(true);
      }
      if (msg.type === "next_task") {
        currentTaskId = msg.task.id;
        setRound(msg.round || "—");
        renderTask(msg.task);
        setRoundActive(true);
      }
      if (msg.type === "round_end") {
        if (typeof msg.player1_score === "number") player1Score = msg.player1_score;
        if (typeof msg.player2_score === "number") player2Score = msg.player2_score;
        setScore(player1Score, player2Score);
        setRoundActive(false);
      }
      if (msg.type === "answer_result") {
        if (msg.is_correct) {
          setNotice(msg.scored ? "Верно! Очко ваше." : "Верно, но очко уже у соперника.", "success");
        } else {
          setNotice("Неверный ответ. Следующий вопрос.", "warn");
        }
      }
      if (msg.type === "match_end") {
        setStatus(`Матч окончен: ${msg.result}`);
        setRoundActive(false);
      }
      if (msg.type === "match_canceled") {
        setStatus(`Матч отменён: ${msg.reason}`);
        setRoundActive(false);
      }
    };
    ws.onclose = () => setStatus("Отключено");
    return ws;
  }

  joinBtn.addEventListener("click", () => {
    const s = ensureWs();
    if (!s) return;
    s.send(JSON.stringify({ type: "queue_join" }));
  });
  leaveBtn.addEventListener("click", () => {
    const s = ensureWs();
    if (!s) return;
    s.send(JSON.stringify({ type: "queue_leave" }));
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    clearNotice();
    const s = ensureWs();
    if (!s) return;
    if (!matchId) { setNotice("Матч ещё не найден.", "warn"); return; }
    if (!roundActive) { setNotice("Дождитесь следующего вопроса.", "warn"); return; }
    const fd = new FormData(form);
    const answer = String(fd.get("answer") || "");
    s.send(JSON.stringify({ type: "answer_submit", match_id: matchId, answer, task_id: currentTaskId }));
    setRoundActive(false);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  applyAuthVisibility();
  bindLogout();
  bindHomeActions();
  bindLoginForm();
  bindRegisterForm();
  loadTasks().catch(() => {});
  loadAnalytics().catch(() => {});
  loadTaskDetail().catch(() => {});
  bindSubmitAnswer();
  bindPvp();
});
