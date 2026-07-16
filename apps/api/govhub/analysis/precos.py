"""GovPricing — pesquisa de preços públicos (agente 22).

Referências extraídas de contratos reais publicados no PNCP (tabela winner_contract).
Regra central: nenhum preço é inventado — toda referência traz fornecedor, órgão,
valor, data de assinatura e UF. Os cenários derivados são insumo para a DECISÃO
HUMANA de preço, nunca o preço em si.
"""
import statistics

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..scoring.fit import _norm, setores_do_objeto
from .winners import WinnerContract


def referencias_para_objeto(session: Session, objeto: str, max_refs: int = 12) -> dict:
    setores_alvo = setores_do_objeto(_norm(objeto))
    refs = []
    for w in session.scalars(select(WinnerContract)).all():
        if not w.valor_global:
            continue
        inter = setores_alvo & set(w.setores or [])
        if inter:
            refs.append({
                "objeto": w.objeto[:120], "valor": w.valor_global,
                "orgao": w.orgao[:45], "uf": w.uf, "fornecedor": w.fornecedor_nome[:40],
                "data": w.data_assinatura, "setores_em_comum": sorted(inter),
                "fonte": "PNCP/contratos", "chave": w.numero_controle.split("|")[0],
            })
    refs.sort(key=lambda r: len(r["setores_em_comum"]), reverse=True)
    refs = refs[:max_refs]
    valores = sorted(r["valor"] for r in refs)
    stats = {}
    if valores:
        stats = {"n": len(valores), "mediana": statistics.median(valores),
                 "minimo": valores[0], "maximo": valores[-1]}
    return {"setores_do_objeto": sorted(setores_alvo), "referencias": refs, "estatisticas": stats,
            "aviso": "Referências públicas para instruir a decisão humana de preço. "
                     "Valores de contratos variam por escopo/duração — comparar objetos antes de usar."}


def secao_orcamento_md(session: Session, objeto: str) -> str:
    r = referencias_para_objeto(session, objeto)
    if not r["referencias"]:
        return ("# Referências de preço\n\nNenhum contrato público comparável na base atual. "
                "Ampliar o período de coleta (`pipeline winners <ini> <fim>`) antes de precificar.\n")
    linhas = "\n".join(
        f"| R$ {x['valor']:,.2f} | {x['data'] or '—'} | {x['uf'] or '--'} | {x['orgao']} | {x['objeto']} |"
        for x in r["referencias"])
    e = r["estatisticas"]
    return f"""# Referências públicas de preço — RASCUNHO_IA (agents/22_PESQUISA_PRECOS)

Setores do objeto: {', '.join(r['setores_do_objeto'])} | Fonte: contratos assinados no PNCP

| Valor global | Assinatura | UF | Órgão | Objeto |
|---|---|---|---|---|
{linhas}

**Estatísticas ({e['n']} referências):** mediana R$ {e['mediana']:,.2f} · mín R$ {e['minimo']:,.2f} · máx R$ {e['maximo']:,.2f}

> {r['aviso']}
> O preço de proposta, o alvo e o piso de lance são ALÇADA HUMANA (registrar aprovação no workflow).
"""
