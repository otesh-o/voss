from typing import Literal

from pydantic import BaseModel, Field


class MessageRecord(BaseModel):
    role: str
    content: str


class ModeRecord(BaseModel):
    name: str
    instruction: str


class AgendaItemRecord(BaseModel):
    id: str
    title: str
    source: str
    time_reference: str | None = None
    status: str
    priority: str
    created_at: str | None = None
    updated_at: str | None = None


class HealthResponse(BaseModel):
    ok: bool
    report: str


class StateResponse(BaseModel):
    mode: str
    modes: list[ModeRecord]
    agenda_count: int
    due_reminder_count: int
    history_count: int


class AgendaResponse(BaseModel):
    items: list[AgendaItemRecord]


class RemindersResponse(BaseModel):
    items: list[AgendaItemRecord]
    due_messages: list[str]


class HistoryResponse(BaseModel):
    items: list[MessageRecord]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class ChatResponse(BaseModel):
    reply: str
    mode: str
    reminders: list[str]
    captured_commitment: AgendaItemRecord | None = None


class TranscribeResponse(BaseModel):
    text: str


class RegisterDeviceRequest(BaseModel):
    push_token: str = Field(min_length=8, max_length=512)
    platform: str = Field(min_length=2, max_length=32)
    device_name: str = Field(min_length=1, max_length=128)


class DeviceRecord(BaseModel):
    push_token: str
    platform: str
    device_name: str


class DevicesResponse(BaseModel):
    items: list[DeviceRecord]


class RuntimeResponse(BaseModel):
    background_active: bool
    reminder_interval_seconds: int


class ModeResponse(BaseModel):
    mode: str
    modes: list[ModeRecord]


class SetModeRequest(BaseModel):
    mode: Literal["build", "review", "strategy", "critical", "quiet"]


class SelfTestResponse(BaseModel):
    report: str
