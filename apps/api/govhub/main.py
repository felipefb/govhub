"""GovHub API — cockpit e workflow (MVP 1).

Toda rota é escopada por tenant. A API nunca envia propostas nem dá lances:
expõe apenas leitura, ingestão de fontes públicas e transições de aprovação
executadas por humanos identificados.
"""
from fastapi import Depends, FastAPI, Form, Header, HTTPException
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


def status_certidao(validade_iso: str, alerta_dias: int = 15) -> tuple[str, str, int]:
    """Retorna (rótulo, classe, dias_restantes) para uma certidão."""
    from datetime import date
    try:
        dias = (date.fromisoformat(validade_iso) - date.today()).days
    except ValueError:
        return ("data inválida", "muted", 0)
    if dias < 0:
        return (f"VENCIDA há {-dias}d", "bad", dias)
    if dias <= alerta_dias:
        return (f"renovar — {dias}d", "warn", dias)
    return (f"válida — {dias}d", "good", dias)


DECISAO_LABEL = {
    "GO": ("GO", "good"), "GO_COM_CONDICOES": ("GO com condições", "warn"),
    "PARCERIA_NECESSARIA": ("Parceria necessária", "info"),
}
ATESTADO_LABEL = {
    "NAO_EXIGE": ("✓ sem atestado", "good"), "EXIGE": ("● exige atestado", "warn"),
    "INDEFINIDO": ("? conferir docs", "muted"),
}


@app.get("/", include_in_schema=False)
def cockpit_html(tenant: str = "avintis", session: Session = Depends(get_session)):
    from fastapi.responses import HTMLResponse

    from .analysis.triage import Triage
    from .approval import ESTADOS
    from .models import Approval as Ap
    from .models import Certificate

    certs = session.scalars(select(Certificate).where(Certificate.tenant_id == tenant)
                            .order_by(Certificate.validade)).all()
    certs_html = "".join(
        (lambda rot, cls, _d: f"<tr><td>{c.nome}</td><td class='muted'>{c.referencia or ''}</td>"
         f"<td>{c.validade}</td><td><span class='badge {cls}'>{rot}</span></td></tr>")
        (*status_certidao(c.validade, c.alerta_dias)) for c in certs)

    aprovacoes = session.scalars(select(Ap).where(Ap.tenant_id == tenant)).all()
    def ap_row(a):
        chips = "".join(
            f"<span class='step {'on' if ESTADOS.index(a.estado) >= i else ''}'>{e.replace('_', ' ').title()}</span>"
            for i, e in enumerate(ESTADOS))
        form = ("" if a.estado == ESTADOS[-1] else
                f"<form method='post' action='/aprovacoes/{a.id}/avancar-form'>"
                f"<input name='ator_humano' placeholder='seu e-mail' required>"
                f"<select name='papel'><option>especialista</option><option>cliente</option>"
                f"<option>representante_legal</option></select>"
                f"<button>Aprovar etapa</button></form>")
        return (f"<tr><td>{a.artefato_tipo}</td><td class='muted'>{a.artefato_ref}</td>"
                f"<td>{chips}</td><td>{form}</td></tr>")
    aprov_html = "".join(ap_row(a) for a in aprovacoes)

    total_opp = session.scalar(select(func.count()).select_from(Opportunity))
    por_decisao = dict(session.execute(
        select(FitScore.decisao_recomendada, func.count())
        .where(FitScore.tenant_id == tenant).group_by(FitScore.decisao_recomendada)
    ).all())
    rows = session.execute(
        select(FitScore, Opportunity, Triage)
        .join(Opportunity, FitScore.opportunity_id == Opportunity.id)
        .outerjoin(Triage, Triage.opportunity_id == Opportunity.id)
        .where(FitScore.tenant_id == tenant, FitScore.decisao_recomendada != "NO_GO")
        .order_by(Opportunity.data_limite.is_(None), Opportunity.data_limite,
                  FitScore.score.desc())
    ).all()
    vivas = [(f, o, tr) for f, o, tr in rows if not tr or tr.vida != "MORTA"]
    mortas = [(f, o, tr) for f, o, tr in rows if tr and tr.vida == "MORTA"]
    pipeline = sum(o.valor_estimado or 0 for f, o, _ in vivas
                   if f.decisao_recomendada in ("GO", "GO_COM_CONDICOES"))

    def linha(f, o, tr):
        dec_txt, dec_cls = DECISAO_LABEL.get(f.decisao_recomendada, (f.decisao_recomendada, "muted"))
        at_txt, at_cls = ATESTADO_LABEL.get(tr.atestado if tr else "INDEFINIDO",
                                            ("? não triado", "muted"))
        ev = (tr.evidencias or {}).get("atestado", "") if tr else ""
        prazo = o.data_limite or (tr.data_sessao if tr else None) or "—"
        return (f"<tr><td><span class='badge {dec_cls}'>{dec_txt}</span></td>"
                f"<td><span class='badge {at_cls}' title='{ev[:200]}'>{at_txt}</span></td>"
                f"<td>{prazo}</td><td class='num'>{f.score:.0f}</td>"
                f"<td class='num'>{'R$ %s' % format(o.valor_estimado, ',.0f') if o.valor_estimado else '—'}</td>"
                f"<td>{o.uf or '—'}</td><td>{(o.orgao or '')[:44]}</td>"
                f"<td class='obj'>{(o.objeto or '')[:110]}</td>"
                f"<td><a href='{o.url_fonte}' target='_blank'>{o.fonte}</a></td></tr>")

    tiles = "".join(
        f"<div class='tile'><div class='n'>{v}</div><div class='l'>{k}</div></div>"
        for k, v in [
            ("monitoradas na base", f"{total_opp:,}".replace(",", ".")),
            ("em disputa viva", len(vivas)),
            ("GO direto", por_decisao.get("GO", 0)),
            ("com condições", por_decisao.get("GO_COM_CONDICOES", 0)),
            ("via parceria", por_decisao.get("PARCERIA_NECESSARIA", 0)),
            ("pipeline disputável", f"R$ {pipeline:,.0f}".replace(",", ".")),
        ])
    from .analysis.partners import sugerir_parceiros
    blocos = []
    for item in sugerir_parceiros(session, tenant):
        linhas_p = "".join(
            f"<tr><td><span class='badge {'good' if p['score'] >= 75 else 'info'}'>{p['score']:.0f}</span></td>"
            f"<td>{p['nome'][:48]}</td><td class='muted'>{p['cnpj']}</td>"
            f"<td class='num'>{p['contratos_recentes']}x</td>"
            f"<td class='num'>R$ {p['valor_recente']:,.0f}</td>"
            f"<td class='muted' style='font-size:.7rem'>{', '.join(f'{k} {v}' for k, v in p['componentes'].items())}</td></tr>"
            for p in item["parceiros"])
        if linhas_p:
            blocos.append(
                f"<p style='margin:.8rem 0 .3rem;font-size:.82rem'><b>[{item['uf']}] "
                f"R$ {item['valor'] or 0:,.0f}</b> — {item['objeto']}</p>"
                f"<table><tr><th>Aceitação</th><th>Empresa</th><th>CNPJ</th><th>Contratos</th>"
                f"<th>Valor recente</th><th>Componentes do score</th></tr>{linhas_p}</table>")
    parcerias_html = "".join(blocos) or "<p class='muted'>nenhuma oportunidade de parceria no funil</p>"

    mortas_html = "".join(
        f"<li><b>{(o.orgao or '')[:40]}</b> — {(o.objeto or '')[:80]} "
        f"<span class='muted'>({(tr.evidencias or {}).get('vida', 'certame encerrado')[:90]}…)</span></li>"
        for f, o, tr in mortas)
    return HTMLResponse(f"""<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>GovHub — Radar Avintis</title><style>
:root{{--ink:#1a2332;--ink2:#5a6676;--line:#e3e8ef;--bg:#f7f9fb;--card:#fff;
--good:#0d7a4f;--goodbg:#e5f5ec;--warn:#8a5a00;--warnbg:#fdf3d9;
--info:#1c5fae;--infobg:#e7f0fb;--mutedbg:#eef1f5}}
*{{box-sizing:border-box}} body{{font-family:system-ui,Segoe UI,sans-serif;margin:0;
color:var(--ink);background:var(--bg)}}
header{{background:var(--card);border-bottom:1px solid var(--line);padding:1rem 2rem;
display:flex;justify-content:space-between;align-items:baseline}}
header h1{{font-size:1.1rem;margin:0}} header .sub{{color:var(--ink2);font-size:.8rem}}
main{{padding:1.5rem 2rem;max-width:1400px;margin:0 auto}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.8rem}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.9rem 1.1rem}}
.tile .n{{font-size:1.5rem;font-weight:700;font-variant-numeric:tabular-nums}}
.tile .l{{color:var(--ink2);font-size:.78rem;margin-top:.15rem}}
h2{{font-size:.95rem;margin:1.6rem 0 .6rem}}
table{{border-collapse:collapse;width:100%;background:var(--card);font-size:.82rem;
border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th{{background:var(--mutedbg);color:var(--ink2);font-weight:600;text-align:left;
padding:.5rem .6rem;font-size:.75rem;text-transform:uppercase;letter-spacing:.03em}}
td{{border-top:1px solid var(--line);padding:.45rem .6rem;vertical-align:top}}
td.num{{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}}
td.obj{{color:var(--ink2)}}
.badge{{display:inline-block;padding:.12rem .5rem;border-radius:99px;font-size:.72rem;
font-weight:600;white-space:nowrap}}
.badge.good{{background:var(--goodbg);color:var(--good)}}
.badge.warn{{background:var(--warnbg);color:var(--warn)}}
.badge.info{{background:var(--infobg);color:var(--info)}}
.badge.muted{{background:var(--mutedbg);color:var(--ink2)}}
.badge.bad{{background:#fde8e8;color:#a02020}}
.step{{display:inline-block;padding:.1rem .45rem;border-radius:4px;font-size:.68rem;
background:var(--mutedbg);color:var(--ink2);margin-right:.2rem}}
.step.on{{background:var(--goodbg);color:var(--good);font-weight:600}}
form{{display:flex;gap:.3rem}} input,select{{border:1px solid var(--line);border-radius:6px;
padding:.25rem .4rem;font-size:.75rem}} button{{background:var(--info);color:#fff;border:0;
border-radius:6px;padding:.25rem .6rem;font-size:.75rem;cursor:pointer}}
.muted{{color:var(--ink2)}} ul{{font-size:.82rem;color:var(--ink)}}
footer{{color:var(--ink2);font-size:.75rem;padding:1rem 2rem;max-width:1400px;margin:0 auto}}
a{{color:var(--info)}}
</style></head><body>
<header><h1>GovHub · Radar de Contratações — Avintis</h1>
<span class='sub'>fontes: PNCP + Compras.gov.br · verificação na fonte primária · triagem documental automática</span></header>
<main>
<div class='tiles'>{tiles}</div>
<h2>Disputa viva — ordenada por prazo</h2>
<table><tr><th>Recomendação</th><th>Qualificação técnica</th><th>Prazo</th><th>Score</th>
<th>Valor est.</th><th>UF</th><th>Órgão</th><th>Objeto</th><th>Fonte</th></tr>
{''.join(linha(f, o, tr) for f, o, tr in vivas)}</table>
<h2>Documentação e certidões — alertas de vencimento</h2>
<table><tr><th>Documento</th><th>Referência</th><th>Validade</th><th>Situação</th></tr>
{certs_html or '<tr><td colspan="4" class="muted">nenhuma certidão cadastrada</td></tr>'}</table>
<h2>Aprovações — Human in the Loop</h2>
<table><tr><th>Artefato</th><th>Referência</th><th>Fluxo (IA → Especialista → Cliente → Aprovado → Enviado)</th><th>Ação</th></tr>
{aprov_html or '<tr><td colspan="4" class="muted">nenhum artefato em aprovação</td></tr>'}</table>
<h2>Parcerias sugeridas — vencedores de TIC com score de aceitação</h2>
{parcerias_html}
<h2>Descartadas pela triagem documental ({len(mortas)})</h2>
<ul>{mortas_html or '<li class="muted">nenhuma</li>'}</ul>
</main>
<footer>Scores e triagens são recomendações de IA com evidência textual dos documentos oficiais
(passe o mouse sobre o selo de qualificação para ver o trecho). Componentes competitivo e jurídico
ainda neutros. A decisão de participação é sempre humana — o sistema não envia propostas nem dá lances.</footer>
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


@app.post("/aprovacoes/{approval_id}/avancar-form", include_in_schema=False)
def avancar_aprovacao_form(approval_id: int,
                           ator_humano: str = Form(...), papel: str = Form(...),
                           session: Session = Depends(get_session)):
    """Variante do cockpit (tenant único até a autenticação — pendência #9)."""
    from fastapi.responses import RedirectResponse
    ap = session.get(Approval, approval_id)
    if not ap:
        raise HTTPException(404, "aprovação não encontrada")
    try:
        avancar(session, ap, ator_humano, papel)
    except ApprovalError as e:
        raise HTTPException(409, str(e))
    return RedirectResponse("/", status_code=303)


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
