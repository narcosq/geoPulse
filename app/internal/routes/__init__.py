"""Global point for collected routers."""
from app.internal.pkg.models import Routes
from app.internal.routes import (
    healthz,
    geolocation,
)

__all__ = ["__routes__"]


__routes__ = Routes(
    routers=(
        healthz.router,
        geolocation.router,
    ),
)
