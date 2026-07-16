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


def enriquecer_detalhes(session: Session, tenant_id: str, timeout: float = 60.0) -> dict:
    """Completa dados faltantes das qualificadas direto na fonte primária:
    data de encerramento de proposta, link do sistema de origem (portal de disputa)
    e situação atual. Não inventa nada: campo sem resposta permanece vazio."""
    import time

    fits = session.scalars(
        select(FitScore).where(FitScore.tenant_id == tenant_id,
                               FitScore.decisao_recomendada != "NO_GO")).all()
    enriquecidas = falhas = 0
    for f in fits:
        opp = session.get(Opportunity, f.opportunity_id)
        raw = opp.raw or {}
        cnpj, ano, seq = (raw.get("orgaoEntidadeCnpj"),
                          raw.get("anoCompraPncp"), raw.get("sequencialCompraPncp"))
        if not (cnpj and ano and seq) or opp.status != "aberta":
            continue
        mudou = {}
        d = {}
        if not opp.data_limite:
            try:
                r = httpx.get(CONSULTA_URL.format(cnpj=cnpj, ano=ano, seq=seq), timeout=timeout)
                r.raise_for_status()
                d = r.json()
            except Exception:
                falhas += 1
                d = {}
            encerr = (d.get("dataEncerramentoProposta") or "")[:10]
            if encerr:
                opp.data_limite = encerr
                mudou["data_limite"] = encerr
            link = d.get("linkSistemaOrigem")
            if link:
                opp.url_fonte = link
                mudou["url_fonte"] = link
        situ = (d.get("situacaoCompraNome") or "").lower()
        if "encerrad" in situ or "homolog" in situ or "anulad" in situ or "revogad" in situ:
            opp.status = "encerrada"
            mudou["status"] = "encerrada"
        else:
            # a situação do PNCP frequentemente fica desatualizada ("Divulgada") mesmo após
            # homologação — a verdade está nos RESULTADOS dos itens (caso UNESP 2026-07-16)
            try:
                rr = httpx.get(
                    f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}"
                    f"/itens/1/resultados", timeout=timeout)
                if rr.status_code == 200 and any(
                        x.get("valorTotalHomologado") and not x.get("dataCancelamento")
                        for x in (rr.json() or [])):
                    opp.status = "encerrada"
                    mudou["status"] = "encerrada (resultado homologado no item)"
            except Exception:
                pass
        if mudou:
            session.add(AuditLog(tenant_id=tenant_id, ator="agents/01_RADAR_CONTRATACOES",
                                 tipo_ator="ia", acao="enriquecimento:pncp",
                                 detalhe={"opportunity_id": opp.id, **mudou}))
            enriquecidas += 1
        time.sleep(0.5)
    session.flush()
    return {"enriquecidas": enriquecidas, "falhas": falhas}


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
