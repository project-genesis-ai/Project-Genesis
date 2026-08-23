from __future__ import annotations

import os
import re

from alembic import context
from sqlalchemy import engine_from_config, pool

from genesis.persistence.models import Base

config = context.config

def _normalize_database_url(url: str) -> str:
    """Normalize and fix Render PostgreSQL URL with SSL."""
    if not url:
        return url
    
    # Fix scheme: postgres:// → postgresql+psycopg://
    url = url.replace("postgres://", "postgresql+psycopg://", 1)
    url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # 🔥 Fix Render hostname: Remove "-a" suffix if present
    # dpg-xxxx-a.oregon-postgres.render.com → dpg-xxxx.oregon-postgres.render.com
    if "@dpg-" in url:
        url = re.sub(
            r'@(dpg-[a-z0-9]+)-a\.oregon-postgres\.render\.com',
            r'@\1.oregon-postgres.render.com',
            url
        )
        # If .oregon-postgres.render.com is missing, add it
        if ".oregon-postgres.render.com" not in url:
            url = re.sub(
                r'@(dpg-[a-z0-9]+)([/?]|$)',
                r'@\1.oregon-postgres.render.com\2',
                url
            )
    
    # Add sslmode=require if missing
    if "sslmode" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"
    
    # Escape % for SQLAlchemy
    return url.replace("%", "%%")

# Set database URL from environment
database_url = os.getenv("DATABASE_URL")
if database_url:
    normalized = _normalize_database_url(database_url)
    config.set_main_option("sqlalchemy.url", normalized)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with SSL support."""
    # 🔥 SSL options ke saath engine banayein
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
