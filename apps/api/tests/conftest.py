import pytest
from govhub.db import make_engine, make_session


@pytest.fixture()
def session():
    SessionLocal = make_session(make_engine("sqlite:///:memory:"))
    with SessionLocal() as s:
        yield s
