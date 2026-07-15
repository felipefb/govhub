"""Fundação de banco: engine, sessão e proteção de imutabilidade do audit_log."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .models import Base


def make_engine(url: str = "sqlite:///govhub.db"):
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
