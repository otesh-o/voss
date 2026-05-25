import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agenda import get_agenda_items
from api_models import (
    AgendaResponse,
    ChatRequest,
    ChatResponse,
    DeviceRecord,
    DevicesResponse,
    HealthResponse,
    HistoryResponse,
    ModeResponse,
    RegisterDeviceRequest,
    RemindersResponse,
    RuntimeResponse,
    SelfTestResponse,
    SetModeRequest,
    StateResponse,
    TranscribeResponse,
)
from background import runner
from config import BACKGROUND_REMINDER_INTERVAL_SECONDS
from core import app_state, chat_turn, collect_and_notify_reminders, startup_report
from devices import list_devices, register_device
from memory import get_history_snapshot
from mode import available_modes_data, get_mode, set_mode
from provider import transcribe_audio_file
from reminder import get_due_reminder_items, preview_due_reminder_messages
from selftest import run_self_test


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "web"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await runner.start()
    try:
        yield
    finally:
        await runner.stop()


app = FastAPI(title="Voss", version="1.0", lifespan=lifespan)
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
        due_messages=preview_due_reminder_messages(),
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


@app.get("/api/devices", response_model=DevicesResponse)
def devices() -> DevicesResponse:
    return DevicesResponse(items=list_devices())


@app.post("/api/devices", response_model=DeviceRecord)
def register_mobile_device(payload: RegisterDeviceRequest) -> DeviceRecord:
    return DeviceRecord(**register_device(payload.model_dump()))


@app.get("/api/runtime", response_model=RuntimeResponse)
def runtime() -> RuntimeResponse:
    return RuntimeResponse(
        background_active=runner.active,
        reminder_interval_seconds=BACKGROUND_REMINDER_INTERVAL_SECONDS,
    )


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...)) -> TranscribeResponse:
    suffix = Path(audio.filename or "voice-input.m4a").suffix or ".m4a"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            shutil.copyfileobj(audio.file, temp_file)
        text = transcribe_audio_file(temp_path)
        if not text:
            raise HTTPException(status_code=422, detail="No speech detected in uploaded audio.")
        return TranscribeResponse(text=text)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await audio.close()
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)


@app.get("/api/self-test", response_model=SelfTestResponse)
def self_test() -> SelfTestResponse:
    return SelfTestResponse(report=run_self_test())


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
