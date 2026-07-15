"""GovHub API — cockpit e workflow (MVP 1).

Toda rota é escopada por tenant. A API nunca envia propostas nem dá lances:
expõe apenas leitura, ingestão de fontes públicas e transições de aprovação
executadas por humanos identificados.
"""
from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .approval import ApprovalError, avancar
from .db import make_engine, make_session
from .models import Approval, Company, FitScore, Opportunity

app = FastAPI(title="GovHub AI", version="0.1.0")
SessionLocal = make_session(make_engine())


def get_session():
    with SessionLocal() as s:
        yield s
        s.commit()


def get_tenant(x_tenant_id: str = Header(...)) -> str:
    return x_tenant_id


@app.get("/oportunidades")
def listar_oportunidades(limit: int = 50, session: Session = Depends(get_session)):
    rows = session.scalars(select(Opportunity).limit(limit)).all()
    return [{
        "id": o.id, "orgao": o.orgao, "uf": o.uf, "municipio": o.municipio,
        "objeto": o.objeto, "modalidade": o.modalidade, "regime_juridico": o.regime_juridico,
        "valor_estimado": o.valor_estimado, "data_limite": o.data_limite,
        "fonte": o.fonte, "url_fonte": o.url_fonte, "status": o.status,
    } for o in rows]


@app.get("/cockpit")
def cockpit(tenant: str = Depends(get_tenant), session: Session = Depends(get_session)):
    por_decisao = dict(session.execute(
        select(FitScore.decisao_recomendada, func.count())
        .where(FitScore.tenant_id == tenant).group_by(FitScore.decisao_recomendada)
    ).all())
    pipeline = session.scalar(
        select(func.coalesce(func.sum(Opportunity.valor_estimado), 0.0))
        .join(FitScore, FitScore.opportunity_id == Opportunity.id)
        .where(FitScore.tenant_id == tenant,
               FitScore.decisao_recomendada.in_(["GO", "GO_COM_CONDICOES"]))
    )
    return {"qualificadas_por_decisao": por_decisao, "valor_pipeline": pipeline}


@app.get("/fit")
def listar_fit(tenant: str = Depends(get_tenant), session: Session = Depends(get_session)):
    rows = session.scalars(select(FitScore).where(FitScore.tenant_id == tenant)).all()
    return [{
        "opportunity_id": f.opportunity_id, "score": f.score,
        "decisao_recomendada": f.decisao_recomendada, "confianca": f.confianca,
        "justificativa": f.justificativa, "componentes": f.componentes,
    } for f in rows]


@app.post("/aprovacoes/{approval_id}/avancar")
def avancar_aprovacao(approval_id: int, ator_humano: str, papel: str,
                      tenant: str = Depends(get_tenant),
                      session: Session = Depends(get_session)):
    ap = session.get(Approval, approval_id)
    if not ap or ap.tenant_id != tenant:
        raise HTTPException(404, "aprovação não encontrada para este tenant")
    try:
        avancar(session, ap, ator_humano, papel)
    except ApprovalError as e:
        raise HTTPException(409, str(e))
    return {"id": ap.id, "estado": ap.estado, "historico": ap.historico}
