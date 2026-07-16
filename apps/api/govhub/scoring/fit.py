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

# fortes: bastam sozinhos. fracas: termos genéricos — exigem 2+ ocorrências para
# ativar a categoria (evita falso GO em "centro de treinamento", "curso de formação de guardas").
TAXONOMIA = {
    # taxonomia revisada em 2026-07-16 contra o CV do responsável técnico
    # (20+ anos: XP/dados financeiros+fraudes, Telefónica/BI, SPES/saúde digital FHIR)
    "inteligencia_artificial": {
        "fortes": ["inteligencia artificial", "ia generativa", "chatbot", "machine learning",
                   "aprendizado de maquina", "assistente virtual", "agentes de inteligencia artificial",
                   "agente de ia", "modelos preditivos", "llm"],
        "fracas": []},
    "dados_analytics": {
        "fortes": ["ciencia de dados", "engenharia de dados", "business intelligence", "power bi",
                   "data lake", "lakehouse", "databricks", "big data", "painel de indicadores",
                   "governanca de dados", "qualidade de dados", "catalogo de dados",
                   "integracao de dados", "pipeline de dados", "anonimizacao", "pseudonimizacao",
                   "prevencao a fraude", "deteccao de fraude", "analise de dados"],
        "fracas": ["analytics", "dashboard", "indicadores", "etl", "data warehouse"]},
    "saude_digital": {
        "fortes": ["prontuario eletronico", "interoperabilidade em saude", "fhir", "e-sus", "rnds",
                   "telessaude", "saude digital", "informatizacao de unidades de saude",
                   "sistema de gestao hospitalar", "dados clinicos"],
        "fracas": ["prontuario", "telemedicina", "regulacao em saude"]},
    "software": {
        "fortes": ["desenvolvimento de software", "fabrica de software", "integracao de sistemas", "sitio eletronico", "sistema de informacao"],
        "fracas": ["portal", "aplicativo", "website", "software"]},
    "automacao": {
        "fortes": ["automacao de processos", "rpa", "atendimento digital", "transformacao digital"],
        "fracas": ["digitalizacao", "automacao"]},
    "capacitacao": {
        "fortes": ["capacitacao de servidores", "treinamento em informatica", "lgpd", "engenharia de prompts"],
        "fracas": ["capacitacao", "treinamento", "curso", "workshop"]},
    # setores do tenant BFSA Trade Law (jurídico/aduaneiro) — "juridica" sozinha é proibida
    # como palavra-chave: colide com "pessoa jurídica" (falso positivo massivo)
    "juridico": {
        "fortes": ["assessoria juridica", "consultoria juridica", "servicos advocaticios",
                   "servicos juridicos", "sociedade de advogados", "parecer juridico",
                   "contencioso judicial", "execucao fiscal", "assessoramento juridico",
                   "consultoria tributaria"],
        "fracas": ["advocacia", "advocaticio", "contencioso"]},
    "aduaneiro_comex": {
        "fortes": ["desembaraco aduaneiro", "despacho aduaneiro", "legislacao aduaneira",
                   "comercio exterior", "comercio internacional", "drawback",
                   "despachante aduaneiro", "agenciamento de cargas"],
        "fracas": ["aduaneiro", "aduaneira", "importacao", "exportacao"]},
}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def _contem(texto: str, termo: str) -> bool:
    import re
    return re.search(rf"\b{re.escape(termo)}\b", texto) is not None


_PRODUTO = ["equipamento", "equipamentos", "aparelho", "aparelhos", "licenca", "licencas",
            "material", "materiais", "mobiliario", "hardware", "impressora", "computadores",
            "notebook", "notebooks", "servidor fisico", "gnss", "camera", "cameras", "kit",
            "suite", "antivirus", "totem", "totens", "sonorizacao",
            "software de apresentacao", "software de apresentacoes", "fitas"]
_SERVICO = ["desenvolvimento", "criacao", "prestacao de servico", "consultoria", "sustentacao",
            "manutencao de software", "integracao de sistemas", "implantacao de solucao",
            "implementacao", "customizacao", "capacitacao", "elaboracao"]
_COMPRA = ["aquisicao de", "fornecimento de", "compra de", "subscricao de licencas",
           "cessao de licenca", "licenciamento de uso de software de terceiro"]


def objeto_e_fornecimento_de_produto(objeto_norm: str) -> bool:
    """Heurística de executabilidade: objeto de compra de produto/licença de terceiro
    (mercado de revenda/fabricante) que uma software house não executa. Serviço junto
    ao objeto (desenvolvimento, implantação...) descaracteriza o bloqueio."""
    compra = any(c in objeto_norm for c in _COMPRA)
    produto = any(_contem(objeto_norm, p) for p in _PRODUTO)
    servico = any(s in objeto_norm for s in _SERVICO)
    return compra and produto and not servico


def setores_do_objeto(objeto_norm: str) -> set[str]:
    ativos = set()
    for cat, kws in TAXONOMIA.items():
        fortes = [k for k in kws["fortes"] if _contem(objeto_norm, k)]
        fracas = [k for k in kws["fracas"] if _contem(objeto_norm, k)]
        if fortes or len(fracas) >= 2:
            ativos.add(cat)
    return ativos


def calcular(session: Session, company: Company, opp: Opportunity) -> FitScore:
    objeto = _norm(opp.objeto)
    setores_empresa = set(company.setores or [])

    # fit técnico: interseção taxonomia do objeto × setores da empresa
    setores_objeto = setores_do_objeto(objeto)
    inter = setores_objeto & setores_empresa
    fit_tecnico = (len(inter) / len(setores_objeto)) if setores_objeto else 0.0

    perfil = company.perfil or {}
    dados_faltantes = []

    # prazo de preparação: menos de 3 dias úteis não dá para habilitar/propor com qualidade
    from datetime import date
    prazo_dias = None
    if opp.data_limite:
        try:
            prazo_dias = (date.fromisoformat(opp.data_limite) - date.today()).days
        except ValueError:
            pass

    doc = perfil.get("completude_documental")
    if doc is None:
        doc = 0.5
        dados_faltantes.append("completude_documental")
    prazo_ok = 1.0 if opp.data_limite else 0.5
    if not opp.data_limite:
        dados_faltantes.append("data_limite")
    valor = opp.valor_estimado
    ticket_max = perfil.get("ticket_max")
    riscos_extra: list[str] = []
    condicoes_extra: list[str] = []
    ticket_min = perfil.get("ticket_min")
    capital_giro = perfil.get("capital_giro")
    if valor is None or ticket_max is None:
        margem = 0.5
        dados_faltantes.append("valor_ou_ticket")
    else:
        margem = 1.0 if valor <= ticket_max else 0.3
        if valor > ticket_max:
            riscos_extra.append(
                f"valor estimado (R$ {valor:,.0f}) acima do teto de habilitação "
                f"econômico-financeira da empresa (R$ {ticket_max:,.0f} ≈ PL × 10)"
            )
        if ticket_min is not None and valor < ticket_min:
            if perfil.get("estrategia_acervo"):
                # fase de formação de acervo: micro-contratos são PRIORIDADE — cada
                # vitória gera atestado público para destravar certames maiores
                condicoes_extra.append(
                    "🎯 ALVO DE ACERVO: valor baixo, esforço pequeno, atestado público na saída"
                )
            else:
                margem = min(margem, 0.5)
                condicoes_extra.append(
                    f"valor abaixo do ticket mínimo (R$ {ticket_min:,.0f}): só vale se gerar "
                    "atestado em setor-alvo com preparação de poucas horas"
                )
        # sem capital de giro: ciclo de caixa penaliza contratos maiores (30-90 dias p/ receber)
        if capital_giro is not None and capital_giro <= 0 and valor > 100000:
            margem = min(margem, 0.6)
            riscos_extra.append(
                "ciclo de caixa: empresa sem capital de giro próprio — exigir pagamento "
                "parcelado/medição mensal ou antecipação contra empenho; conferir se o "
                "edital exige garantia (evitar)"
            )

    # benefícios LC 123/2006 para ME/EPP: empate ficto e exclusividade até R$ 80 mil
    competitiva = 0.5
    if perfil.get("porte") in ("ME", "EPP") and valor is not None and valor <= 80000:
        competitiva = 0.65
        condicoes_extra.append(
            "verificar se o certame é exclusivo ME/EPP (LC 123/2006, até R$ 80 mil) "
            "— vantagem competitiva relevante"
        )

    componentes = {
        "fit_tecnico": round(fit_tecnico, 2),
        "capacidade_documental": doc,
        "margem_estimada": margem,
        "probabilidade_competitiva": competitiva,  # neutro salvo benefício ME/EPP; agente 04 refinará
        "complexidade_operacional": 0.5,    # neutro até Leitura de Edital (agente 08)
        "risco_juridico": 0.5,              # neutro até Agente Jurídico (agente 09)
        "prazo_preparacao": prazo_ok,
        "valor_estrategico": 0.5,
    }
    dados_faltantes += ["probabilidade_competitiva", "complexidade_operacional", "risco_juridico"]

    score = round(sum(componentes[k] * PESOS[k] for k in PESOS) * 100, 1)
    confianca = round(max(0.1, 1.0 - 0.1 * len(dados_faltantes)), 2)

    inexigibilidade = "inexigibilidade" in _norm(opp.modalidade or "")
    if inexigibilidade:
        # contratação direta de fornecedor já definido: não há disputa possível
        decisao = "NO_GO"
        riscos_extra.append("inexigibilidade: fornecedor já definido pelo órgão, sem disputa")
    elif prazo_dias is not None and prazo_dias < 3:
        decisao = "NO_GO"
        riscos_extra.append(
            f"prazo insuficiente: {prazo_dias} dia(s) até o encerramento — "
            "inviável preparar habilitação e proposta com qualidade")
    elif objeto_e_fornecimento_de_produto(objeto):
        decisao = "NO_GO"
        riscos_extra.append(
            "objeto é fornecimento de produto/licença de terceiro (mercado de revenda/"
            "fabricante) — não é serviço executável por software house")
    elif fit_tecnico == 0:
        decisao = "NO_GO"
    elif (valor is not None and ticket_max is not None and valor > ticket_max
          and (perfil.get("interesse_consorcio") or perfil.get("interesse_subcontratacao"))):
        # objeto aderente porém acima da capacidade própria: buscar parceiro em vez de descartar
        decisao = "PARCERIA_NECESSARIA"
        condicoes_extra.append(
            "consórcio (se o edital permitir) ou subcontratação para complementar "
            "habilitação econômico-financeira e acervo técnico"
        )
    elif score >= 70:
        decisao = "GO"
    elif score >= 50:
        decisao = "GO_COM_CONDICOES"
    elif score >= 35:
        decisao = "PARCERIA_NECESSARIA"
    else:
        decisao = "NO_GO"

    if decisao != "NO_GO" and prazo_dias is not None and 3 <= prazo_dias <= 7:
        condicoes_extra.append(f"prazo apertado ({prazo_dias} dias): priorizar imediatamente")

    fs = FitScore(
        tenant_id=company.tenant_id, company_id=company.id, opportunity_id=opp.id,
        score=score, componentes=componentes,
        justificativa=(
            f"Setores do objeto: {sorted(setores_objeto) or 'nenhum reconhecido'}; "
            f"interseção com a empresa: {sorted(inter) or 'nenhuma'}. "
            f"Dados faltantes reduziram a confiança: {sorted(set(dados_faltantes))}."
        ),
        riscos=riscos_extra + [f"componente neutro pendente de análise: {d}" for d in
                               ("complexidade_operacional", "risco_juridico")],
        condicoes=condicoes_extra
        + (["complementar capacidade via parceria"] if decisao == "PARCERIA_NECESSARIA" else []),
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
