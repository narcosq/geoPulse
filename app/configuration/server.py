"""Server configuration."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configuration.events import on_startup
from app.configuration.events import on_shutdown

from app.pkg.logger.tracing import setup_tracing
from app.pkg.models.base import BaseAPIException
from app.pkg.settings import settings

from app.internal.routes import __routes__
from app.internal.pkg.middlewares.handle_http_exceptions import handle_api_exceptions
from app.internal.pkg.middlewares.validation_error_handler import create_validation_error_handlers
from app.internal.pkg.middlewares.correlation import CorrelationMiddleware
from app.internal.pkg.middlewares.localization import LocalizationMiddleware

__all__ = ["Server"]


class Server:
    """Register all requirements for correct work of server instance."""

    __app: FastAPI
    __app_name: str = settings.API_INSTANCE_APP_NAME

    def __init__(self, app: FastAPI):
        self.__app = app
        self._register_traces(app)
        self._register_routes(app)
        self._register_events(app)
        self._register_middlewares(app)
        self._register_http_exceptions(app)

    def get_app(self) -> FastAPI:
        """Get current application instance.

        Returns: ``FastAPI`` application instance.
        """
        return self.__app

    @staticmethod
    def _register_events(app: FastAPI) -> None:
        """Register on startup events.

        Args:
            app: ``FastAPI`` application instance.

        Returns: None
        """

        app.on_event("startup")(on_startup)
        app.on_event("shutdown")(on_shutdown)

    def _register_traces(self, app: FastAPI) -> None:
        """Register traces for open telemetry.

        Args:
            app: ``FastAPI`` application instance.

        Returns: None
        """
        _, self.__app = setup_tracing(
            app=app,
            service_name=settings.API_INSTANCE_APP_NAME,
            service_version=settings.API_INSTANCE_VERSION,
            otlp_endpoint=settings.OTLP_ENDPOINT,
            environment=settings.API_INSTANCE_STAGE,
            sentry_dsn=settings.SENTRY_DSN,
        )

    @staticmethod
    def _register_routes(app: FastAPI) -> None:
        """Include routers in ``FastAPI`` instance from ``__routes__``.

        Args:
            app: ``FastAPI`` application instance.

        Returns: None
        """

        __routes__.register_routes(app)

    @staticmethod
    def _register_http_exceptions(app: FastAPI) -> None:
        """Register http exceptions.

        FastAPIInstance handle BaseApiExceptions raises inside functions.

        Args:
            app: ``FastAPI`` application instance

        Returns: None
        """

        # Register localized validation error handlers
        handlers = create_validation_error_handlers()
        for handler_config in handlers:
            app.add_exception_handler(
                handler_config["exception"],
                handler_config["handler"]
            )

        app.add_exception_handler(BaseAPIException, handle_api_exceptions)

    @staticmethod
    def __register_cors_origins(app: FastAPI) -> None:
        """Register cors origins."""

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _register_middlewares(self, app) -> None:
        """Apply routes middlewares."""

        self.__register_cors_origins(app)
        app.add_middleware(LocalizationMiddleware)
        app.add_middleware(CorrelationMiddleware)
