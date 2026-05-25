import type {
  AgendaResponse,
  ChatResponse,
  HealthState,
  HistoryResponse,
  ModeResponse,
  RegisterDeviceRequest,
  RemindersResponse,
  RuntimeResponse,
  TranscribeResponse,
} from "./types";

function normalizeBaseUrl(baseUrl: string) {
  return baseUrl.trim().replace(/\/+$/, "");
}

async function getJson<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${normalizeBaseUrl(baseUrl)}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function fetchHealth(baseUrl: string) {
  return getJson<HealthState>(baseUrl, "/api/health");
}

export function fetchModeState(baseUrl: string) {
  return getJson<ModeResponse>(baseUrl, "/api/mode");
}

export function fetchAgenda(baseUrl: string) {
  return getJson<AgendaResponse>(baseUrl, "/api/agenda");
}

export function fetchReminders(baseUrl: string) {
  return getJson<RemindersResponse>(baseUrl, "/api/reminders");
}

export function fetchHistory(baseUrl: string) {
  return getJson<HistoryResponse>(baseUrl, "/api/history");
}

export function fetchRuntime(baseUrl: string) {
  return getJson<RuntimeResponse>(baseUrl, "/api/runtime");
}

export function setVossMode(baseUrl: string, mode: string) {
  return getJson<ModeResponse>(baseUrl, "/api/mode", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ mode }),
  });
}

export function chatWithVoss(baseUrl: string, message: string) {
  return getJson<ChatResponse>(baseUrl, "/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });
}

export function registerDevice(baseUrl: string, payload: RegisterDeviceRequest) {
  return getJson(baseUrl, "/api/devices", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function transcribeAudio(baseUrl: string, audioUri: string) {
  const formData = new FormData();
  formData.append("audio", {
    uri: audioUri,
    name: "voss-mobile-input.m4a",
    type: "audio/m4a",
  } as unknown as Blob);

  return getJson<TranscribeResponse>(baseUrl, "/api/transcribe", {
    method: "POST",
    body: formData,
  });
}
