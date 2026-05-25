const healthEl = document.getElementById("health");
const modeEl = document.getElementById("mode");
const modeSelectEl = document.getElementById("mode-select");
const agendaEl = document.getElementById("agenda");
const agendaCountEl = document.getElementById("agenda-count");
const remindersEl = document.getElementById("reminders");
const reminderCountEl = document.getElementById("reminder-count");
const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");

function addMessage(role, text) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = `${role === "user" ? "You" : "Voss"}: ${text}`;
  messagesEl.appendChild(item);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderAgenda(items) {
  if (!items.length) {
    agendaEl.textContent = "No open agenda items.";
    return;
  }

  agendaEl.textContent = items
    .map((item) => {
      const timeRef = item.time_reference || "unspecified";
      return `${item.id} | ${item.title} | time=${timeRef} | status=${item.status} | priority=${item.priority}`;
    })
    .join("\n");
}

function renderReminders(items) {
  if (!items.length) {
    remindersEl.textContent = "No reminders are currently due.";
    return;
  }

  remindersEl.textContent = items
    .map((item) => {
      const timeRef = item.time_reference || "unspecified";
      return `${item.id} | ${item.title} | ${timeRef} | ${item.status}`;
    })
    .join("\n");
}

function renderModes(currentMode, modes) {
  modeEl.textContent = currentMode;
  modeSelectEl.innerHTML = "";

  for (const mode of modes) {
    const option = document.createElement("option");
    option.value = mode.name;
    option.textContent = mode.name;
    option.selected = mode.name === currentMode;
    modeSelectEl.appendChild(option);
  }
}

async function loadState() {
  const [healthRes, stateRes, agendaRes, remindersRes, historyRes] = await Promise.all([
    fetch("/api/health"),
    fetch("/api/state"),
    fetch("/api/agenda"),
    fetch("/api/reminders"),
    fetch("/api/history"),
  ]);

  const health = await healthRes.json();
  const state = await stateRes.json();
  const agenda = await agendaRes.json();
  const reminders = await remindersRes.json();
  const history = await historyRes.json();

  healthEl.textContent = health.ok ? "System ready." : "System needs attention.";
  renderModes(state.mode, state.modes);
  agendaCountEl.textContent = `${state.agenda_count} open item${state.agenda_count === 1 ? "" : "s"}`;
  reminderCountEl.textContent = `${state.due_reminder_count} due reminder${state.due_reminder_count === 1 ? "" : "s"}`;
  renderAgenda(agenda.items);
  renderReminders(reminders.items);
  messagesEl.innerHTML = "";
  for (const entry of history.items) {
    addMessage(entry.role === "assistant" ? "assistant" : "user", entry.content);
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = inputEl.value.trim();
  if (!message) return;

  addMessage("user", message);
  inputEl.value = "";

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await response.json();
  addMessage("assistant", data.reply);
  await loadState();
});

modeSelectEl.addEventListener("change", async () => {
  await fetch("/api/mode", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: modeSelectEl.value }),
  });
  await loadState();
});

loadState().catch((error) => {
  healthEl.textContent = `Failed to load: ${error}`;
});
