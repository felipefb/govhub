"""Núcleo de ingestão compartilhado: idempotente, com quarentena e trilha de auditoria."""
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuditLog, Opportunity, QuarantineRecord

OBRIGATORIOS = ("orgao", "objeto", "modalidade", "chave_fonte")


def classificar_regime(amparo_legal: str | None) -> str:
    a = amparo_legal or ""
    if "13.303" in a:
        return "lei_13303_2016"
    if "14.133" in a:
        return "lei_14133_2021"
    return "lei_14133_2021"  # default do ecossistema PNCP


def ingerir(session: Session, fonte: str, agente: str,
            mapear: Callable[[dict], dict], registros: list[dict]) -> dict:
    novos = atualizados = quarentena = 0
    for raw in registros:
        c = mapear(raw)
        faltando = [k for k in OBRIGATORIOS if not c.get(k)]
        if faltando:
            session.add(QuarantineRecord(fonte=fonte, motivo=f"campos ausentes: {faltando}", raw=raw))
            quarentena += 1
            continue
        existente = session.scalar(
            select(Opportunity).where(
                Opportunity.fonte == fonte, Opportunity.chave_fonte == c["chave_fonte"]
            )
        )
        if existente:
            if (existente.raw or {}).get("_objeto_corrigido"):
                # correção documental manual tem precedência sobre o espelho
                c.pop("objeto", None)
                raw = {**raw, "_objeto_corrigido": True}
            for k, v in c.items():
                setattr(existente, k, v)
            existente.raw = raw
            atualizados += 1
        else:
            session.add(Opportunity(**c, raw=raw, data_coleta=datetime.now(timezone.utc)))
            novos += 1
    session.add(AuditLog(
        tenant_id="_plataforma", ator=agente, tipo_ator="ia",
        acao=f"ingestao:{fonte}",
        detalhe={"novos": novos, "atualizados": atualizados, "quarentena": quarentena},
    ))
    session.flush()
    return {"novos": novos, "atualizados": atualizados, "quarentena": quarentena}


class FonteIndisponivel(Exception):
    """A fonte oficial está fora do ar: gera alerta operacional, nunca dado inventado."""


def get_com_retry(url: str, params: dict, timeout: float = 60.0, tentativas: int = 3):
    import time

    import httpx

    ultimo_erro = None
    for i in range(tentativas):
        try:
            r = httpx.get(url, params=params, timeout=timeout, headers={"accept": "*/*"})
            if r.status_code >= 500:
                ultimo_erro = f"HTTP {r.status_code}"
            else:
                r.raise_for_status()
                return r
        except (httpx.TimeoutException, httpx.TransportError) as e:
            ultimo_erro = repr(e)
        time.sleep(2 ** i)
    raise FonteIndisponivel(f"{url} indisponível após {tentativas} tentativas: {ultimo_erro}")
