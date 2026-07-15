"""Fit score (Sprint 03) — heurística explicável v1, conforme schemas/fit_score.schema.json.

Regras: pesos declarados; falta de dados reduz a confiança, nunca é preenchida
silenciosamente; a decisão final de participação é sempre humana
(aprovador_humano nasce nulo).
"""
import unicodedata

from sqlalchemy.orm import Session

from ..models import AuditLog, Company, FitScore, Opportunity

VERSAO = "fit-v1"
MODELO = "heuristica-taxonomia-v1"
VERSAO_PROMPT = "n/a (regra determinística)"

PESOS = {
    "fit_tecnico": 0.25,
    "capacidade_documental": 0.15,
    "margem_estimada": 0.15,
    "probabilidade_competitiva": 0.15,
    "complexidade_operacional": 0.10,
    "risco_juridico": 0.10,
    "prazo_preparacao": 0.05,
    "valor_estrategico": 0.05,
}

TAXONOMIA = {
    "inteligencia_artificial": ["inteligencia artificial", "ia generativa", "chatbot", "machine learning", "assistente virtual"],
    "dados_analytics": ["ciencia de dados", "engenharia de dados", "analytics", "business intelligence", "power bi", "data lake", "painel de indicadores", "dashboard", "governanca de dados"],
    "software": ["desenvolvimento de software", "fabrica de software", "sistema de informacao", "portal", "aplicativo", "integracao de sistemas", "website", "sitio eletronico"],
    "automacao": ["automacao de processos", "rpa", "digitalizacao", "atendimento digital", "transformacao digital"],
    "capacitacao": ["capacitacao", "treinamento", "curso", "workshop", "lgpd"],
}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def calcular(session: Session, company: Company, opp: Opportunity) -> FitScore:
    objeto = _norm(opp.objeto)
    setores_empresa = set(company.setores or [])

    # fit técnico: interseção taxonomia do objeto × setores da empresa
    setores_objeto = {cat for cat, kws in TAXONOMIA.items() if any(k in objeto for k in kws)}
    inter = setores_objeto & setores_empresa
    fit_tecnico = (len(inter) / len(setores_objeto)) if setores_objeto else 0.0

    perfil = company.perfil or {}
    dados_faltantes = []

    doc = perfil.get("completude_documental")
    if doc is None:
        doc = 0.5
        dados_faltantes.append("completude_documental")
    prazo_ok = 1.0 if opp.data_limite else 0.5
    if not opp.data_limite:
        dados_faltantes.append("data_limite")
    valor = opp.valor_estimado
    ticket_max = perfil.get("ticket_max")
    if valor is None or ticket_max is None:
        margem = 0.5
        dados_faltantes.append("valor_ou_ticket")
    else:
        margem = 1.0 if valor <= ticket_max else 0.3

    componentes = {
        "fit_tecnico": round(fit_tecnico, 2),
        "capacidade_documental": doc,
        "margem_estimada": margem,
        "probabilidade_competitiva": 0.5,   # neutro até Inteligência Competitiva (agente 04)
        "complexidade_operacional": 0.5,    # neutro até Leitura de Edital (agente 08)
        "risco_juridico": 0.5,              # neutro até Agente Jurídico (agente 09)
        "prazo_preparacao": prazo_ok,
        "valor_estrategico": 0.5,
    }
    dados_faltantes += ["probabilidade_competitiva", "complexidade_operacional", "risco_juridico"]

    score = round(sum(componentes[k] * PESOS[k] for k in PESOS) * 100, 1)
    confianca = round(max(0.1, 1.0 - 0.1 * len(dados_faltantes)), 2)

    if fit_tecnico == 0:
        decisao = "NO_GO"
    elif score >= 70:
        decisao = "GO"
    elif score >= 50:
        decisao = "GO_COM_CONDICOES"
    elif score >= 35:
        decisao = "PARCERIA_NECESSARIA"
    else:
        decisao = "NO_GO"

    fs = FitScore(
        tenant_id=company.tenant_id, company_id=company.id, opportunity_id=opp.id,
        score=score, componentes=componentes,
        justificativa=(
            f"Setores do objeto: {sorted(setores_objeto) or 'nenhum reconhecido'}; "
            f"interseção com a empresa: {sorted(inter) or 'nenhuma'}. "
            f"Dados faltantes reduziram a confiança: {sorted(set(dados_faltantes))}."
        ),
        riscos=[f"componente neutro pendente de análise: {d}" for d in
                ("probabilidade_competitiva", "complexidade_operacional", "risco_juridico")],
        condicoes=(["complementar capacidade via parceria"] if decisao == "PARCERIA_NECESSARIA" else []),
        decisao_recomendada=decisao, versao=VERSAO, modelo=MODELO,
        versao_prompt=VERSAO_PROMPT, confianca=confianca, aprovador_humano=None,
    )
    session.add(fs)
    session.add(AuditLog(
        tenant_id=company.tenant_id, ator="agents/07_FIT_COMERCIAL", tipo_ator="ia",
        acao="fit_score:calculado",
        detalhe={"opportunity_id": opp.id, "score": score, "decisao": decisao, "confianca": confianca},
    ))
    session.flush()
    return fs
