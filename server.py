from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agenda import get_agenda_items
from api_models import (
    AgendaResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    HistoryResponse,
    ModeResponse,
    RemindersResponse,
    SelfTestResponse,
    SetModeRequest,
    StateResponse,
)
from core import app_state, chat_turn, collect_and_notify_reminders, startup_report
from memory import get_history_snapshot
from mode import available_modes_data, get_mode, set_mode
from reminder import get_due_reminder_items
from selftest import run_self_test


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "web"

app = FastAPI(title="Voss", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    ok, report = startup_report()
    return HealthResponse(ok=ok, report=report)


@app.get("/api/state", response_model=StateResponse)
def state() -> StateResponse:
    return StateResponse(**app_state())


@app.get("/api/history", response_model=HistoryResponse)
def history() -> HistoryResponse:
    return HistoryResponse(items=get_history_snapshot())


@app.get("/api/agenda", response_model=AgendaResponse)
def agenda() -> AgendaResponse:
    return AgendaResponse(items=get_agenda_items())


@app.get("/api/reminders", response_model=RemindersResponse)
def reminders() -> RemindersResponse:
    return RemindersResponse(
        items=get_due_reminder_items(),
        due_messages=collect_and_notify_reminders(),
    )


@app.get("/api/mode", response_model=ModeResponse)
def mode() -> ModeResponse:
    return ModeResponse(mode=get_mode(), modes=available_modes_data())


@app.post("/api/mode", response_model=ModeResponse)
def update_mode(payload: SetModeRequest) -> ModeResponse:
    set_mode(payload.mode)
    return ModeResponse(mode=get_mode(), modes=available_modes_data())


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return ChatResponse(**chat_turn(payload.message))


@app.get("/api/self-test", response_model=SelfTestResponse)
def self_test() -> SelfTestResponse:
    return SelfTestResponse(report=run_self_test())


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
