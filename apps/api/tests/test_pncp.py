"""Sprint 02 — testes de aceite: dedup, quarentena, regime jurídico."""
from sqlalchemy import select

from govhub.ingestion.pncp import ingerir, mapear
from govhub.models import Opportunity, QuarantineRecord

RAW_OK = {
    "numeroControlePNCP": "00000000000000-1-000001/2026",
    "orgaoEntidade": {"razaoSocial": "Prefeitura Municipal de Teste"},
    "unidadeOrgao": {"ufSigla": "SP", "municipioNome": "Campinas"},
    "objetoCompra": "Contratação de serviços de business intelligence e Power BI",
    "modalidadeNome": "Pregão - Eletrônico",
    "valorTotalEstimado": 250000.0,
    "dataEncerramentoProposta": "2026-08-10T09:00:00",
    "linkSistemaOrigem": "https://exemplo.gov.br/edital/1",
}
RAW_INCOMPLETO = {"numeroControlePNCP": "x-2/2026", "objetoCompra": "sem órgão"}


def test_mapeamento_canonico():
    c = mapear(RAW_OK)
    assert c["orgao"] == "Prefeitura Municipal de Teste"
    assert c["regime_juridico"] == "lei_14133_2021"
    assert c["data_limite"] == "2026-08-10"


def test_ingestao_idempotente_com_quarentena(session):
    r1 = ingerir(session, [RAW_OK, RAW_INCOMPLETO])
    assert r1 == {"novos": 1, "atualizados": 0, "quarentena": 1}
    r2 = ingerir(session, [RAW_OK])
    assert r2 == {"novos": 0, "atualizados": 1, "quarentena": 0}
    assert len(session.scalars(select(Opportunity)).all()) == 1
    q = session.scalars(select(QuarantineRecord)).one()
    assert "campos ausentes" in q.motivo
