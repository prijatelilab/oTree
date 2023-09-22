import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import prijateli_tree.app.models.database as models
from prijateli_tree.app.utils.constants import KEY_DATABASE_URI


config = context.config
config.set_main_option(
    "sqlalchemy.url",
    os.getenv(
        KEY_DATABASE_URI,
        "postgresql://postgres:password_password@localhost/prijateli_tree",
    ),
)

fileConfig(config.config_file_name)

target_metadata = models.Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in `offline` mode."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in `online` mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()