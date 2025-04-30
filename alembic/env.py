import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# load models and settings required for migrations
from app.db.base import Base
from app.core.config import settings
from app.models.tree import Node  # explicitly import models for migrations

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
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# set database url from application settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def pre_migration_checks():
    """perform checks before running migrations."""
    # verify database connection
    from sqlalchemy import create_engine
    engine = create_engine(settings.DATABASE_URL)
    try:
        with engine.connect() as conn:
            pass
    except Exception as e:
        raise Exception(f"Failed to connect to database: {e}")
    
    # verify all models are imported
    if not Node.__table__ in target_metadata.tables.values():
        raise Exception("Node model not properly registered in metadata")

def post_migration_tasks(connection):
    """perform tasks after migrations complete."""
    # verify table existence
    inspector = inspect(connection)
    required_tables = ['nodes']
    for table in required_tables:
        if not inspector.has_table(table):
            raise Exception(f"Required table {table} not created after migration")
    
    # verify indexes
    indexes = inspector.get_indexes('nodes')
    required_indexes = ['ix_nodes_id', 'ix_nodes_label', 'ix_nodes_parent_id']
    existing_indexes = [idx['name'] for idx in indexes]
    for idx in required_indexes:
        if idx not in existing_indexes:
            raise Exception(f"Required index {idx} not created after migration")

def run_migrations_offline() -> None:
    """generates sql migration commands without database connection.
    
    creates migration sql by using only the database url. this allows
    generating migration scripts without a live database.
    """
    url = config.get_main_option("sqlalchemy.url")
    pre_migration_checks()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """runs migrations using an active database connection.
    
    executes all pending migrations within a transaction using
    the provided database connection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # compare column types during migrations
        compare_server_default=True,  # compare default values
    )

    with context.begin_transaction():
        context.run_migrations()
        post_migration_tasks(connection)


def run_migrations_online() -> None:
    """applies migrations to a live database.
    
    uses an existing database connection if available, otherwise creates
    a new engine and connection to run migrations. ensures proper cleanup
    of database resources.
    """
    pre_migration_checks()
    
    connectable = context.config.attributes.get("connection", None)

    if connectable is None:
        connectable = config.attributes.get("connection", None)

    if connectable is None:
        # create new engine only if no existing connection
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)
    else:
        do_run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
