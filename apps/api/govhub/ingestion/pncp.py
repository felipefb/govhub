"""Conector PNCP (Sprint 02) — API pública de consulta.

Idempotente: upsert por (fonte, numeroControlePNCP). Registros sem campos
obrigatórios vão para quarentena, nunca são completados silenciosamente.
"""
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuditLog, Opportunity, QuarantineRecord

BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
FONTE = "pncp"
OBRIGATORIOS = ("orgao", "objeto", "modalidade", "chave_fonte")


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
        # PNCP publica contratações regidas pela Lei 14.133/2021; estatais têm marcação própria.
        "regime_juridico": "lei_13303_2016" if raw.get("modoDisputaNome") == "Fechado-Estatal"
        else "lei_14133_2021",
        "valor_estimado": raw.get("valorTotalEstimado"),
        "data_limite": (raw.get("dataEncerramentoProposta") or "")[:10] or None,
        "status": "aberta",
        "momento_demanda": "oportunidade_aberta",
        "url_fonte": raw.get("linkSistemaOrigem")
        or f"https://pncp.gov.br/app/editais?q={raw.get('numeroControlePNCP', '')}",
    }


def ingerir(session: Session, registros: list[dict]) -> dict:
    novos = atualizados = quarentena = 0
    for raw in registros:
        c = mapear(raw)
        faltando = [k for k in OBRIGATORIOS if not c.get(k)]
        if faltando:
            session.add(QuarantineRecord(fonte=FONTE, motivo=f"campos ausentes: {faltando}", raw=raw))
            quarentena += 1
            continue
        existente = session.scalar(
            select(Opportunity).where(
                Opportunity.fonte == FONTE, Opportunity.chave_fonte == c["chave_fonte"]
            )
        )
        if existente:
            for k, v in c.items():
                setattr(existente, k, v)
            existente.raw = raw
            atualizados += 1
        else:
            session.add(Opportunity(**c, raw=raw, data_coleta=datetime.now(timezone.utc)))
            novos += 1
    session.add(AuditLog(
        tenant_id="_plataforma", ator="agents/01_RADAR_CONTRATACOES", tipo_ator="ia",
        acao="ingestao:pncp",
        detalhe={"novos": novos, "atualizados": atualizados, "quarentena": quarentena},
    ))
    session.flush()
    return {"novos": novos, "atualizados": atualizados, "quarentena": quarentena}


class FonteIndisponivel(Exception):
    """A fonte oficial está fora do ar: gera alerta operacional, nunca dado inventado."""


def buscar(data_inicial: str, data_final: str, modalidade: int = 6, pagina: int = 1,
           tamanho_pagina: int = 50, timeout: float = 60.0, tentativas: int = 3) -> list[dict]:
    """Consulta a API pública do PNCP (datas AAAAMMDD; modalidade 6 = pregão eletrônico).

    Faz retry com backoff; 5xx/timeout persistente vira FonteIndisponivel.
    """
    import time

    params = {
        "dataInicial": data_inicial, "dataFinal": data_final,
        "codigoModalidadeContratacao": modalidade, "pagina": pagina,
        "tamanhoPagina": tamanho_pagina,
    }
    ultimo_erro = None
    for i in range(tentativas):
        try:
            r = httpx.get(BASE_URL, params=params, timeout=timeout)
            if r.status_code == 204 or not r.content:
                return []
            if r.status_code >= 500:
                ultimo_erro = f"HTTP {r.status_code}"
            else:
                r.raise_for_status()
                return r.json().get("data", [])
        except (httpx.TimeoutException, httpx.TransportError) as e:
            ultimo_erro = repr(e)
        time.sleep(2 ** i)
    raise FonteIndisponivel(f"PNCP indisponível após {tentativas} tentativas: {ultimo_erro}")
