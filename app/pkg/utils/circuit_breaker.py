import asyncio
from typing import Any, Callable, Awaitable, Literal

__all__ = ["AsyncCircuitBreaker", "CircuitOpenError"]


class CircuitOpenError(RuntimeError):
    pass


class AsyncCircuitBreaker:
    def __init__(
        self,
        max_failures: int = 5,
        reset_timeout_seconds: float = 30.0,
    ) -> None:
        self.max_failures = max_failures
        self.reset_timeout_seconds = reset_timeout_seconds
        self._failure_count = 0
        self._state: Literal["CLOSED", "OPEN", "HALF_OPEN"] = "CLOSED"
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    async def _can_pass(self) -> bool:
        if self._state == "CLOSED":
            return True
        if self._state == "OPEN":
            if self._opened_at is None:
                return False
            if (asyncio.get_event_loop().time() - self._opened_at) >= self.reset_timeout_seconds:
                self._state = "HALF_OPEN"
                return True
            return False
        return True

    async def call(self, func: Callable[[], Awaitable[Any]]) -> Any:
        async with self._lock:
            can_pass = await self._can_pass()
            if not can_pass:
                raise CircuitOpenError("CircuitBreaker: OPEN state")
            probing = self._state == "HALF_OPEN"
        try:
            result = await func()
        except Exception:
            async with self._lock:
                self._failure_count += 1
                if self._failure_count >= self.max_failures or probing:
                    self._state = "OPEN"
                    self._opened_at = asyncio.get_event_loop().time()
                else:
                    self._state = "CLOSED"
                self._failure_count = min(self._failure_count, self.max_failures)
            raise
        else:
            async with self._lock:
                self._failure_count = 0
                self._state = "CLOSED"
                self._opened_at = None
            return result 