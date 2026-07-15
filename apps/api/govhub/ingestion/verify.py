"""Verificação contra a fonte primária (PNCP consulta).

O espelho dadosabertos.compras.gov.br pode divergir do PNCP oficial (caso real:
Detran-DF 2026/34, objeto trocado). Toda oportunidade qualificada (não NO_GO)
é reconferida no PNCP; divergência corrige o registro e invalida o score.
"""
import unicodedata

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuditLog, FitScore, Opportunity

CONSULTA_URL = "https://pncp.gov.br/api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{seq}"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def verificar_qualificadas(session: Session, tenant_id: str, timeout: float = 60.0) -> dict:
    fits = session.scalars(
        select(FitScore).where(FitScore.tenant_id == tenant_id,
                               FitScore.decisao_recomendada != "NO_GO")
    ).all()
    ok = corrigidas = falhas = 0
    for f in fits:
        opp = session.get(Opportunity, f.opportunity_id)
        raw = opp.raw or {}
        cnpj, ano, seq = (raw.get("orgaoEntidadeCnpj"),
                          raw.get("anoCompraPncp"), raw.get("sequencialCompraPncp"))
        if not (cnpj and ano and seq):
            falhas += 1
            continue
        import time

        oficial = None
        for tentativa in range(3):
            try:
                r = httpx.get(CONSULTA_URL.format(cnpj=cnpj, ano=ano, seq=seq), timeout=timeout)
                if r.status_code == 200:
                    oficial = r.json()
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1 + tentativa)
        if oficial is None:
            session.add(AuditLog(
                tenant_id=tenant_id, ator="agents/09_DATA_QUALITY_VERIFY", tipo_ator="ia",
                acao="verificacao_pncp:falha_consulta",
                detalhe={"opportunity_id": opp.id, "chave": opp.chave_fonte,
                         "acao_requerida": "conferir manualmente no portal PNCP"},
            ))
            falhas += 1
            continue
        time.sleep(0.5)  # cortesia com a API pública
        objeto_oficial = oficial.get("objetoCompra") or ""
        if _norm(objeto_oficial)[:120] != _norm(opp.objeto)[:120]:
            detalhe = {
                "opportunity_id": opp.id, "chave": opp.chave_fonte,
                "objeto_espelho": (opp.objeto or "")[:200],
                "objeto_oficial": objeto_oficial[:200],
            }
            opp.objeto = objeto_oficial
            session.delete(f)  # score baseado em dado errado é inválido
            session.add(AuditLog(
                tenant_id=tenant_id, ator="agents/09_DATA_QUALITY_VERIFY", tipo_ator="ia",
                acao="verificacao_pncp:divergencia_corrigida", detalhe=detalhe,
            ))
            corrigidas += 1
        else:
            ok += 1
    session.add(AuditLog(
        tenant_id=tenant_id, ator="agents/09_DATA_QUALITY_VERIFY", tipo_ator="ia",
        acao="verificacao_pncp:concluida",
        detalhe={"confirmadas": ok, "corrigidas": corrigidas, "falhas": falhas},
    ))
    session.flush()
    return {"confirmadas": ok, "corrigidas": corrigidas, "falhas": falhas}
