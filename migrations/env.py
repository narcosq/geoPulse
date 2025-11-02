import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Load environment variables from .env file
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models' MetaData object here
# This is needed for 'autogenerate' support
# Example:
# from app.pkg.db.base import Base
# target_metadata = Base.metadata
try:
    from app.pkg.db.base import Base  # type: ignore
    # Ensure models module is imported so models are registered
    import app.pkg.db.models  # noqa: F401
    target_metadata = Base.metadata
except Exception:
    target_metadata = None

# Try to resolve DSN from app settings if env var is missing
try:
    from app.pkg.settings.settings import get_settings  # type: ignore
except Exception:  # pragma: no cover - alembic context import timing
    get_settings = None  # type: ignore


def _resolve_database_url() -> str:
    url = os.getenv("POSTGRES_DSN")
    if url:
        return url
    if get_settings is not None:
        try:
            settings = get_settings()
            return settings.POSTGRES.DSN  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: F841
            pass
    raise ValueError("Database DSN not found. Set POSTGRES_DSN or configure app settings.")


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = _resolve_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This function creates an Engine and runs migrations.
    """
    from sqlalchemy import create_engine
    
    url = _resolve_database_url()
    
    # Replace 'asyncpg' with 'psycopg2' for synchronous operations
    sync_url = url.replace("asyncpg", "psycopg2")
    
    connectable = create_engine(sync_url)

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
