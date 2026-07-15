"""Fundação de banco: engine, sessão e proteção de imutabilidade do audit_log."""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

# banco dev ancorado em apps/api, independente do CWD; produção usa GOVHUB_DATABASE_URL
_DEFAULT_URL = os.environ.get(
    "GOVHUB_DATABASE_URL",
    f"sqlite:///{(Path(__file__).resolve().parent.parent / 'govhub.db').as_posix()}",
)


def make_engine(url: str = _DEFAULT_URL):
    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    if url.startswith("sqlite"):
        with engine.begin() as conn:
            for op in ("UPDATE", "DELETE"):
                conn.exec_driver_sql(
                    f"""CREATE TRIGGER IF NOT EXISTS audit_no_{op.lower()}
                        BEFORE {op} ON audit_log
                        BEGIN SELECT RAISE(ABORT, 'audit_log é imutável'); END;"""
                )
    return engine


def make_session(engine) -> sessionmaker:
    return sessionmaker(engine, expire_on_commit=False, future=True)
