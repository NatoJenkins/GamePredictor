"""Database engine and table access."""
import os
from sqlalchemy import create_engine, MetaData, Table
from dotenv import load_dotenv

load_dotenv()

_engine = None
_metadata = MetaData()


def get_engine():
    """Get or create SQLAlchemy engine from DATABASE_URL env var."""
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL environment variable not set")
        _engine = create_engine(url)
    return _engine


def get_table(table_name: str, engine=None) -> Table:
    """Reflect and return a table from the database."""
    eng = engine or get_engine()
    return Table(table_name, _metadata, autoload_with=eng)
