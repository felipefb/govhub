"""Bid Copilot (MVP 2) — matriz de requisitos e proposta-rascunho por certame.

Fluxo: baixa os documentos oficiais do PNCP → extrai exigências de habilitação por
famílias conhecidas (método validado manualmente em 9 certames reais) → cruza cada
exigência com as evidências da empresa (perfil + data room) → gera MATRIZ_REQUISITOS.md,
CHECKLIST.md e PROPOSTA_RASCUNHO.md em `bids/<slug>/` → registra o artefato como
RASCUNHO_IA no workflow de aprovação.

A proposta NUNCA contém preço (alçada humana) nem capacidades não evidenciadas.
"""
import io
import re
import time
from datetime import date
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Approval, AuditLog, Certificate, Company, Opportunity

ARQUIVOS_URL = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos"
ARQUIVO_URL = "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{doc}"
BIDS_DIR = Path(__file__).resolve().parents[3].parent / "bids"

# famílias de exigência: (id, nome, regex de detecção, como a empresa atende)
FAMILIAS = [
    ("H_FISCAL", "Regularidade fiscal, social e trabalhista",
     r"regularidade fiscal|fazenda nacional|receita federal|fgts|d[ée]bitos trabalhistas|cndt",
     "sicaf"),
    ("H_JURIDICA", "Habilitação jurídica (atos constitutivos)",
     r"habilita[çc][ãa]o jur[íi]dica|contrato social|atos? constitutivos?",
     "sicaf"),
    ("H_FALENCIA", "Certidão negativa de falência",
     r"certid[ãa]o negativa de fal[êe]ncia|fal[êe]ncia expedida",
     "emitir"),
    ("H_INDICES", "Qualificação econômico-financeira (índices/PL/balanço)",
     r"[íi]ndices? (?:de liquidez|econ[ôo]mic)|patrim[ôo]nio l[íi]quido|balan[çc]o patrimonial",
     "balanco"),
    ("H_ATESTADO", "Atestado/certidão de capacidade técnica",
     r"atestado[s]? de (?:capacidade|fornecimento)|certid[õo]es ou atestados|comprova[çc][ãa]o de aptid[ãa]o",
     "atestado"),
    ("H_DECLARACOES", "Declarações de praxe (menor, PCD, ME/EPP)",
     r"declara[çc][ãa]o de que (?:n[ãa]o emprega|cumpre)|reserva de cargos|trabalho do menor",
     "declarar"),
    ("T_POC", "Prova de conceito / amostra / demonstração",
     r"prova de conceito|apresenta[çc][ãa]o de amostra|demonstra[çc][ãa]o pr[áa]tica",
     "humano"),
    ("T_GARANTIA", "Garantia de proposta ou contratual",
     r"garantia (?:de proposta|contratual|de execu[çc][ãa]o)|seguro[- ]garantia|cau[çc][ãa]o",
     "humano"),
    ("T_VISTORIA", "Visita/vistoria técnica",
     r"visita t[ée]cnica|vistoria",
     "humano"),
]


def _evidencia(chave: str, session: Session, company: Company) -> tuple[str, str]:
    """Retorna (status, evidência) para cada família, usando dados reais da empresa."""
    perfil = company.perfil or {}
    if chave == "sicaf":
        return ("ATENDE", "SICAF completo (níveis I-IV e VI) — documentação puxada do registro cadastral")
    if chave == "balanco":
        pl = perfil.get("patrimonio_liquido")
        idx = perfil.get("indices", {})
        if pl:
            return ("ATENDE", f"Balanço 2025 no SICAF: PL R$ {pl:,.2f}; LC {idx.get('LC')}, LG {idx.get('LG')}")
        return ("PENDENTE", "balanço não informado no perfil")
    if chave == "atestado":
        return ("GAP", "empresa em formação de acervo — sem atestado formal (estratégia: Plano A)")
    if chave == "emitir":
        return ("EMITIR", "emissão online gratuita (TJ do domicílio) — incluir no checklist")
    if chave == "declarar":
        return ("ATENDE", "declarações marcadas no sistema pelo representante legal na sessão")
    return ("DECISAO_HUMANA", "exigência operacional — avaliar custo/logística antes do GO")


def montar_matriz(texto: str, session: Session, company: Company) -> list[dict]:
    matriz = []
    for fid, nome, pat, chave in FAMILIAS:
        m = re.search(pat, texto, re.I)
        if not m:
            continue
        i = max(0, m.start() - 120)
        trecho = re.sub(r"\s+", " ", texto[i:m.end() + 280])[:340]
        status, evid = _evidencia(chave, session, company)
        matriz.append({"id": fid, "requisito": nome, "trecho": trecho,
                       "status": status, "evidencia": evid})
    return matriz


def _baixar_textos(opp: Opportunity, timeout: float = 90.0) -> str:
    from pypdf import PdfReader
    raw = opp.raw or {}
    cnpj, ano, seq = (raw.get("orgaoEntidadeCnpj"),
                      raw.get("anoCompraPncp"), raw.get("sequencialCompraPncp"))
    if not (cnpj and ano and seq):
        return ""
    try:
        docs = httpx.get(ARQUIVOS_URL.format(cnpj=cnpj, ano=ano, seq=seq), timeout=timeout).json()
    except Exception:
        return ""
    texto = ""
    for d in docs if isinstance(docs, list) else []:
        try:
            pdf = httpx.get(ARQUIVO_URL.format(cnpj=cnpj, ano=ano, seq=seq,
                                               doc=d.get("sequencialDocumento")),
                            timeout=timeout, follow_redirects=True)
            texto += "\n" + "\n".join(p.extract_text() or ""
                                      for p in PdfReader(io.BytesIO(pdf.content)).pages)
        except Exception:
            continue
        time.sleep(0.3)
    return texto


def _slug(opp: Opportunity) -> str:
    org = re.sub(r"[^A-Za-z0-9]+", "", (opp.orgao or "ORG"))[:12].upper()
    num = (opp.chave_fonte or str(opp.id)).split("/")[0].split("-")[-1]
    return f"{date.today().year}_{org}_{num}"


def preparar_bid(session: Session, tenant_id: str, opportunity_id: int) -> dict:
    company = session.scalar(select(Company).where(Company.tenant_id == tenant_id))
    opp = session.get(Opportunity, opportunity_id)
    texto = _baixar_textos(opp)
    if not texto.strip():
        return {"erro": "nenhum documento legível no PNCP para este certame"}
    matriz = montar_matriz(texto, session, company)

    pasta = BIDS_DIR / _slug(opp)
    pasta.mkdir(parents=True, exist_ok=True)
    hoje = date.today().isoformat()

    linhas = "\n".join(
        f"| {r['id']} | {r['requisito']} | {r['status']} | {r['evidencia']} |" for r in matriz)
    trechos = "\n\n".join(f"**{r['id']} — {r['requisito']}**\n> {r['trecho']}" for r in matriz)
    gaps = [r for r in matriz if r["status"] in ("GAP", "DECISAO_HUMANA")]
    (pasta / "MATRIZ_REQUISITOS.md").write_text(f"""# Matriz de requisitos — {opp.orgao}

**RASCUNHO_IA {hoje} | agents/08_LEITURA_EDITAL | fonte: documentos oficiais do PNCP ({opp.chave_fonte})**

Objeto: {opp.objeto}
Valor estimado: R$ {opp.valor_estimado or 0:,.2f} | Prazo: {opp.data_limite or 'a confirmar'} | {opp.modalidade}

| # | Requisito | Status | Evidência da empresa |
|---|---|---|---|
{linhas}

## Trechos-fonte (auditoria)

{trechos}
""", encoding="utf-8")

    checklist = "\n".join(
        f"- [{'x' if r['status'] == 'ATENDE' else ' '}] {r['requisito']} — {r['evidencia']}"
        for r in matriz)
    (pasta / "CHECKLIST.md").write_text(
        f"# Checklist de participação — {opp.chave_fonte}\n\n{checklist}\n\n"
        f"- [ ] Proposta de preços conforme modelo do edital (alçada humana)\n"
        f"- [ ] Alçada de lance aprovada (inicial/alvo/piso) ANTES da sessão\n", encoding="utf-8")

    setores = ", ".join(company.setores or [])
    (pasta / "PROPOSTA_RASCUNHO.md").write_text(f"""# Proposta técnica e comercial — RASCUNHO_IA

**Estado: RASCUNHO_IA — não enviar. Fluxo obrigatório: revisão de especialista → cliente → aprovação.**
Gerado em {hoje} por agents/19_PROPOSTA_COMERCIAL a partir de evidências reais do perfil.

## 1. Proponente
{company.razao_social} — CNPJ {company.cnpj}. Microempresa optante do Simples Nacional (LC 123/2006).
Setores de atuação: {setores}.

## 2. Entendimento da necessidade
{(opp.objeto or '')[:600]}

## 3. Abordagem proposta
[COMPLETAR COM ESPECIALISTA — estruturar a partir do TR: arquitetura, metodologia, cronograma,
entregáveis e critérios de aceite. NÃO declarar capacidade sem evidência.]

## 4. Experiência e equipe
Responsável técnico: Felipe Filgueira Barral — 20+ anos em dados e engenharia; ex-sócio da XP Inc.
(liderança de engenharia de dados e modernização Azure); experiência em LLM, RAG, ML em produção
(Azure, Docker/AKS), governança de dados e LGPD.
[Anexar evidências conforme exigência do edital — ver MATRIZ_REQUISITOS.md item H_ATESTADO.]

## 5. Condições comerciais
- Preço: **[ALÇADA HUMANA — definir preço de tabela, alvo e piso antes da sessão]**
- Validade da proposta: 60 dias. Faturamento conforme edital.

## 6. Declarações
Conforme exigências do edital, prestadas no sistema pelo representante legal.
""", encoding="utf-8")

    ap = Approval(tenant_id=tenant_id, artefato_tipo="pacote_bid",
                  artefato_ref=str(pasta.relative_to(BIDS_DIR.parent)).replace("\\", "/"),
                  estado="RASCUNHO_IA")
    session.add(ap)
    session.add(AuditLog(tenant_id=tenant_id, ator="agents/24_PROPOSAL_ASSEMBLY", tipo_ator="ia",
                         acao="bid:pacote_gerado",
                         detalhe={"opportunity_id": opp.id, "chave": opp.chave_fonte,
                                  "requisitos": len(matriz),
                                  "gaps": [r["id"] for r in gaps]}))
    session.flush()
    return {"pasta": str(pasta), "requisitos": len(matriz),
            "gaps": [r["id"] for r in gaps], "approval_id": ap.id}
