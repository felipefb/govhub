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


@app.get("/", include_in_schema=False)
def cockpit_html(tenant: str = "avintis", session: Session = Depends(get_session)):
    from fastapi.responses import HTMLResponse

    total_opp = session.scalar(select(func.count()).select_from(Opportunity))
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
    top = session.execute(
        select(FitScore, Opportunity)
        .join(Opportunity, FitScore.opportunity_id == Opportunity.id)
        .where(FitScore.tenant_id == tenant, FitScore.decisao_recomendada != "NO_GO")
        .order_by(FitScore.score.desc()).limit(25)
    ).all()
    linhas = "".join(
        f"<tr><td>{f.score:.1f}</td><td>{f.decisao_recomendada}</td><td>{o.uf or ''}</td>"
        f"<td>{(o.orgao or '')[:50]}</td><td>{(o.objeto or '')[:120]}</td>"
        f"<td>{'R$ %.0f' % o.valor_estimado if o.valor_estimado else '—'}</td>"
        f"<td>{o.data_limite or '—'}</td>"
        f"<td><a href='{o.url_fonte}' target='_blank'>{o.fonte}</a></td></tr>"
        for f, o in top
    )
    cards = "".join(
        f"<div class='card'><div class='n'>{v}</div><div>{k}</div></div>"
        for k, v in [("oportunidades monitoradas", total_opp),
                     ("GO", por_decisao.get("GO", 0)),
                     ("GO COM CONDIÇÕES", por_decisao.get("GO_COM_CONDICOES", 0)),
                     ("PARCERIA NECESSÁRIA", por_decisao.get("PARCERIA_NECESSARIA", 0)),
                     ("pipeline qualificado", f"R$ {pipeline:,.0f}")]
    )
    return HTMLResponse(f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>
<title>GovHub AI — Cockpit</title><style>
body{{font-family:system-ui;margin:2rem;color:#1a2332;background:#f6f8fa}}
h1{{font-size:1.4rem}} .cards{{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}}
.card{{background:#fff;border:1px solid #dde3ea;border-radius:8px;padding:1rem 1.5rem}}
.card .n{{font-size:1.6rem;font-weight:700}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:.85rem}}
th,td{{border:1px solid #dde3ea;padding:.4rem .6rem;text-align:left}}
th{{background:#eef2f6}} .nota{{color:#667;font-size:.8rem;margin-top:1rem}}
</style></head><body>
<h1>GovHub AI — Cockpit · tenant: {tenant}</h1>
<div class='cards'>{cards}</div>
<table><tr><th>Score</th><th>Recomendação</th><th>UF</th><th>Órgão</th><th>Objeto</th>
<th>Valor estimado</th><th>Prazo</th><th>Fonte</th></tr>{linhas}</table>
<p class='nota'>Scores são recomendações de IA (heurística v1) com componentes neutros pendentes
de análise jurídica e competitiva. A decisão de participação é sempre humana.</p>
</body></html>""")


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
