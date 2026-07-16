"""Partner Matching (agente 27) — sugere parceiros para oportunidades PARCERIA_NECESSARIA.

Cruza cada oportunidade com os vencedores reais de contratos TIC (winner_contract)
e calcula um SCORE DE ACEITAÇÃO 0-100: a probabilidade estimada de a parceria fazer
sentido para AMBOS os lados, com componentes declarados e explicáveis.

Componentes:
- aderencia_setorial (0-35): setores do objeto ∩ setores dos contratos do parceiro;
- porte_compativel (0-25): o parceiro já executa contratos na ordem de grandeza do objeto;
- maquina_de_vencer (0-20): múltiplos contratos recentes = estrutura de licitação ativa;
- proximidade_uf (0-10): contrato recente na mesma UF do certame;
- complementaridade_avintis (0-10): parceiro forte no objeto porém o objeto pede IA/dados
  (o que a Avintis agrega) — parceria com papel claro para os dois.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import FitScore, Opportunity
from ..scoring.fit import _norm, setores_do_objeto
from .winners import WinnerContract

AVINTIS_SETORES = {"inteligencia_artificial", "dados_analytics", "software", "automacao"}


def _perfis_vencedores(session: Session) -> list[dict]:
    perfis: dict[str, dict] = {}
    for w in session.scalars(select(WinnerContract)).all():
        p = perfis.setdefault(w.fornecedor_cnpj, {
            "cnpj": w.fornecedor_cnpj, "nome": w.fornecedor_nome, "contratos": 0,
            "valor_total": 0.0, "maior_contrato": 0.0, "ufs": set(), "setores": set()})
        p["contratos"] += 1
        p["valor_total"] += w.valor_global or 0
        p["maior_contrato"] = max(p["maior_contrato"], w.valor_global or 0)
        p["ufs"].add(w.uf or "?")
        p["setores"].update(w.setores or [])
    return list(perfis.values())


def score_aceitacao(opp: Opportunity, parceiro: dict) -> tuple[float, dict]:
    setores_opp = setores_do_objeto(_norm(opp.objeto)) or set()
    inter = setores_opp & parceiro["setores"]
    c = {}
    c["aderencia_setorial"] = round(35 * (len(inter) / len(setores_opp)), 1) if setores_opp else 0
    valor = opp.valor_estimado or 0
    if valor and parceiro["maior_contrato"]:
        razao = parceiro["maior_contrato"] / valor
        c["porte_compativel"] = 25 if 0.2 <= razao <= 20 else (12 if razao > 20 else 5)
    else:
        c["porte_compativel"] = 8
    c["maquina_de_vencer"] = min(20, 10 * (parceiro["contratos"] - 1) + 5)
    c["proximidade_uf"] = 10 if opp.uf in parceiro["ufs"] else 0
    c["complementaridade_avintis"] = 10 if (setores_opp & AVINTIS_SETORES) else 0
    return round(sum(c.values()), 1), c


def sugerir_parceiros(session: Session, tenant_id: str, top_n: int = 3,
                      score_minimo: float = 40) -> list[dict]:
    perfis = _perfis_vencedores(session)
    out = []
    fits = session.execute(
        select(FitScore, Opportunity)
        .join(Opportunity, FitScore.opportunity_id == Opportunity.id)
        .where(FitScore.tenant_id == tenant_id,
               FitScore.decisao_recomendada == "PARCERIA_NECESSARIA")
    ).all()
    for f, o in fits:
        ranked = sorted((( *score_aceitacao(o, p), p) for p in perfis),
                        key=lambda x: -x[0])
        sugestoes = [{"nome": p["nome"], "cnpj": p["cnpj"], "score": s,
                      "componentes": comp, "contratos_recentes": p["contratos"],
                      "valor_recente": p["valor_total"]}
                     for s, comp, p in ranked[:top_n] if s >= score_minimo]
        out.append({"opportunity_id": o.id, "objeto": (o.objeto or "")[:110],
                    "valor": o.valor_estimado, "uf": o.uf, "parceiros": sugestoes})
    return out
