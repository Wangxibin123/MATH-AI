from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

# ★ 指向工程里的 engine 和 SQLModel
import pathlib  # noqa: E402
import sys  # noqa: E402

# Add project root to sys.path to allow importing apps.gateway.db
# Assuming env.py is in apps/gateway/alembic, and project root is 3 levels up.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import SQLModel  # ★ # noqa: E402
from sqlmodel.sql.sqltypes import (  # noqa: E402
    GUID,
    AutoString,
)  # MODIFIED: Import AutoString

from apps.gateway.db import (  # noqa: E402
    DB_URL,
)  # ★ Changed from engine to DB_URL as per typical alembic setup

# Import all models to ensure they are registered with SQLModel metadata
from apps.gateway.models import *  # noqa: F401, F403, E402 ★ Import all models

target_metadata = SQLModel.metadata  # ★
config.set_main_option(
    "sqlalchemy.url", DB_URL
)  # ★ Set the sqlalchemy.url from our db.py


# Custom render_item function for SQLModel types
def render_item(type_, obj, autogen_context):
    """Render an item for autogenerate."""
    rendered_type = None
    if type_ == "type":
        if isinstance(obj, GUID):
            rendered_type = "sa.UUID"
        elif isinstance(obj, AutoString):
            rendered_type = "sa.String"  # Render AutoString as sa.String
        # Add more SQLModel specific types here if needed

    if rendered_type is not None:
        autogen_context.imports.add("import sqlalchemy as sa")
        return rendered_type

    return False  # Default rendering for other types


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
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
