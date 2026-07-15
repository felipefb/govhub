"""Conector PNCP (Sprint 02) — API pública de consulta.

Idempotente: upsert por (fonte, numeroControlePNCP). Registros sem campos
obrigatórios vão para quarentena, nunca são completados silenciosamente.
"""
from sqlalchemy.orm import Session

from .core import FonteIndisponivel, classificar_regime, get_com_retry
from .core import ingerir as _ingerir

__all__ = ["buscar", "ingerir", "mapear", "FonteIndisponivel", "BASE_URL", "FONTE"]

BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
FONTE = "pncp"


def mapear(raw: dict) -> dict:
    """Mapeia o payload do PNCP para o contrato canônico (schemas/opportunity.schema.json)."""
    orgao = (raw.get("orgaoEntidade") or {}).get("razaoSocial")
    unidade = raw.get("unidadeOrgao") or {}
    return {
        "fonte": FONTE,
        "chave_fonte": raw.get("numeroControlePNCP"),
        "orgao": orgao,
        "uf": unidade.get("ufSigla"),
        "municipio": unidade.get("municipioNome"),
        "objeto": raw.get("objetoCompra"),
        "modalidade": raw.get("modalidadeNome"),
        "regime_juridico": classificar_regime((raw.get("amparoLegal") or {}).get("nome")),
        "valor_estimado": raw.get("valorTotalEstimado"),
        "data_limite": (raw.get("dataEncerramentoProposta") or "")[:10] or None,
        "status": "aberta",
        "momento_demanda": "oportunidade_aberta",
        "url_fonte": raw.get("linkSistemaOrigem")
        or f"https://pncp.gov.br/app/editais?q={raw.get('numeroControlePNCP', '')}",
    }


def ingerir(session: Session, registros: list[dict]) -> dict:
    return _ingerir(session, FONTE, "agents/01_RADAR_CONTRATACOES", mapear, registros)


def buscar(data_inicial: str, data_final: str, modalidade: int = 6, pagina: int = 1,
           tamanho_pagina: int = 50, timeout: float = 60.0, tentativas: int = 3) -> list[dict]:
    """Consulta a API pública do PNCP (datas AAAAMMDD; modalidade 6 = pregão eletrônico)."""
    r = get_com_retry(BASE_URL, {
        "dataInicial": data_inicial, "dataFinal": data_final,
        "codigoModalidadeContratacao": modalidade, "pagina": pagina,
        "tamanhoPagina": tamanho_pagina,
    }, timeout=timeout, tentativas=tentativas)
    if r.status_code == 204 or not r.content:
        return []
    return r.json().get("data", [])
