import asyncio
from contextlib import suppress

from config import BACKGROUND_REMINDER_INTERVAL_SECONDS
from core import collect_and_notify_reminders


class BackgroundRunner:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._active = False

    @property
    def active(self) -> bool:
        return self._active and self._task is not None and not self._task.done()

    async def start(self):
        if self.active:
            return
        self._active = True
        self._task = asyncio.create_task(self._loop(), name="voss-background-reminders")

    async def stop(self):
        self._active = False
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _loop(self):
        while self._active:
            try:
                collect_and_notify_reminders()
            except Exception:
                pass
            await asyncio.sleep(BACKGROUND_REMINDER_INTERVAL_SECONDS)


runner = BackgroundRunner()
