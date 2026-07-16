"""Alertas de certidão e componentes do cockpit."""
from datetime import date, timedelta

from govhub.main import status_certidao


def _d(dias):
    return (date.today() + timedelta(days=dias)).isoformat()


def test_certidao_valida():
    rot, cls, dias = status_certidao(_d(90))
    assert cls == "good" and dias == 90


def test_certidao_em_alerta():
    rot, cls, _ = status_certidao(_d(10), alerta_dias=15)
    assert cls == "warn" and "renovar" in rot


def test_certidao_vencida():
    rot, cls, _ = status_certidao(_d(-3))
    assert cls == "bad" and "VENCIDA" in rot
