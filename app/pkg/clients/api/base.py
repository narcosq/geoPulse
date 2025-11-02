import abc
import asyncio
from typing import Any, Literal

import pydantic
from aiohttp import ClientSession, ClientResponse

from app.pkg.logger import logger
from app.pkg.utils.circuit_breaker import AsyncCircuitBreaker
from app.pkg.settings.settings import get_settings

__all__ = ["BaseApiClient"]

settings = get_settings()


class BaseApiClient(abc.ABC):
    """Base client for api."""
    kwargs: dict[str, Any]
    client_name: str

    _client: ClientSession

    def __init__(
        self,
        base_url: pydantic.AnyUrl,
        client_name: str,
        max_failures: int = settings.CIRCUIT_BREAKER.MAX_FAILURES,
        reset_timeout_seconds: float = settings.CIRCUIT_BREAKER.RESET_TIMEOUT_SECONDS,
        **kwargs
    ):
        self._client = ClientSession(base_url=str(base_url))
        self.client_name = client_name
        self.kwargs = kwargs

        self._circuit_breaker = AsyncCircuitBreaker(
            max_failures=max_failures,
            reset_timeout_seconds=reset_timeout_seconds,
        )

    async def make_request(
        self,
        path: str,
        method: Literal["POST", "GET", "PUT", "DELETE"],
        **kwargs,
    ) -> ClientResponse:
        """Make request to chat api."""
        logger.info(
            "[%(client_name)s] [request]: <%(method)s> %(path)s %(kwargs)s",
            {
                "client_name": self.client_name,
                "method": method,
                "path": path,
                "kwargs": kwargs,
            }
        )

        async def _do_request() -> ClientResponse:
            async with self._client.request(
                method, path, **kwargs
            ) as response:
                logger.info(
                    "[%(client_name)s] [response]: <%(status)s> %(body)s",
                    {
                        "client_name": self.client_name,
                        "status": response.status,
                        "body": (await response.text())[:400],
                    }
                )
                return response

        return await self._circuit_breaker.call(_do_request)

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.create_task(self._client.close())
            else:
                return loop.run_until_complete(self._client.close())
        except RuntimeError as e:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(self._client.close())

    async def __aenter__(self) -> "BaseApiClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.close()
