from logging.config import fileConfig
import pathlib
import sys

# -------- 提前把项目根塞进 sys.path --------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# -------- 之后的 import 全部加 noqa: E402 --------
from alembic import context  # noqa: E402
from sqlalchemy import engine_from_config, pool  # noqa: E402

from apps.gateway.settings import settings  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.sql.sqltypes import GUID, AutoString  # noqa: E402
from apps.gateway.models import *  # noqa: E402,F401,F403

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

target_metadata = SQLModel.metadata  # ★
config.set_main_option(
    "sqlalchemy.url",
    settings.SQLALCHEMY_DATABASE_URI,  # ★ Use URI from settings
)


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
