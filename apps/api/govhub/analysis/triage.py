"""Triagem documental das oportunidades qualificadas (pendências #19 e #20).

Para cada oportunidade não-NO_GO, baixa os documentos oficiais do PNCP e extrai:
- exigência de atestado/qualificação técnica (NAO_EXIGE / EXIGE / INDEFINIDO);
- sinais de certame morto (sem disputa, contratada definida, homologado);
- data da sessão/encerramento quando localizável.

Método validado manualmente em 7 certames reais em 2026-07-15.
Toda classificação guarda o trecho-evidência; INDEFINIDO exige leitura humana.
"""
import io
import re
import time

import httpx
from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..models import AuditLog, Base, Opportunity

ARQUIVOS_URL = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos"
ARQUIVO_URL = "https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{doc}"

RE_NAO_EXIGE = re.compile(
    r"n[ãa]o (?:haver[áa]|ser[áa] exigid[ao]|se exigir[áa])[^.]{0,140}"
    r"(?:qualifica[çc][ãa]o t[ée]cnica|atestado)", re.I)
RE_EXIGE = re.compile(
    r"(?:atestado[s]? de capacidade t[ée]cnica|certid[õo]es ou atestados"
    r"|comprova[çc][ãa]o de aptid[ãa]o)", re.I)
RE_MORTO = re.compile(
    r"sem disputa|termo de homologa[çc][ãa]o|homologo o presente|adjudicad[oa] [àa]"
    r"|contratada[:\s]+\d{2}\.\d{3}\.\d{3}/", re.I)
# sinais documentais que alimentam complexidade operacional e risco jurídico (pendência #6)
RE_SINAIS = {
    "garantia_exigida": re.compile(
        r"garantia (?:de proposta|contratual|de execu[çc][ãa]o)|seguro[- ]garantia|cau[çc][ãa]o", re.I),
    "poc_ou_amostra": re.compile(
        r"prova de conceito|apresenta[çc][ãa]o de amostra|demonstra[çc][ãa]o pr[áa]tica", re.I),
    "vistoria_presencial": re.compile(r"visita t[ée]cnica|vistoria", re.I),
    "sla_formal": re.compile(r"n[íi]veis? de servi[çc]o|acordo de n[íi]vel|\bSLA\b", re.I),
    "cessao_pi": re.compile(r"propriedade intelectual|direitos? autorais", re.I),
    "subcontratacao_vedada": re.compile(r"vedada? a subcontrata[çc][ãa]o", re.I),
    "consorcio_vedado": re.compile(r"n[ãa]o (?:ser[áa] admitid|se admitir)[ao][^.]{0,40}cons[óo]rcio", re.I),
}

RE_SESSAO = re.compile(
    r"(?:data da sess[ãa]o|sess[ãa]o p[úu]blica|fase de lances|encerramento[^\n]{0,40})"
    r"[^\n]{0,60}?(\d{2}/\d{2}/\d{4})", re.I)


class Triage(Base):
    __tablename__ = "triage"
    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(index=True, unique=True)
    atestado: Mapped[str] = mapped_column(String)      # NAO_EXIGE | EXIGE | INDEFINIDO
    vida: Mapped[str] = mapped_column(String)          # VIVA | MORTA | INDEFINIDA
    data_sessao: Mapped[str | None] = mapped_column(String, nullable=True)
    evidencias: Mapped[dict] = mapped_column(JSON, default=dict)


def _texto_pdf(conteudo: bytes) -> str:
    from pypdf import PdfReader
    try:
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(conteudo)).pages)
    except Exception:
        return ""


def triar_oportunidade(opp: Opportunity, timeout: float = 90.0) -> dict:
    raw = opp.raw or {}
    cnpj, ano, seq = (raw.get("orgaoEntidadeCnpj"),
                      raw.get("anoCompraPncp"), raw.get("sequencialCompraPncp"))
    resultado = {"atestado": "INDEFINIDO", "vida": "INDEFINIDA",
                 "data_sessao": None, "evidencias": {}}
    if not (cnpj and ano and seq):
        return resultado
    try:
        docs = httpx.get(ARQUIVOS_URL.format(cnpj=cnpj, ano=ano, seq=seq), timeout=timeout).json()
    except Exception as e:
        resultado["evidencias"]["erro"] = repr(e)[:120]
        return resultado
    texto_total = ""
    for d in docs if isinstance(docs, list) else []:
        try:
            pdf = httpx.get(ARQUIVO_URL.format(cnpj=cnpj, ano=ano, seq=seq,
                                               doc=d.get("sequencialDocumento")),
                            timeout=timeout, follow_redirects=True)
            texto_total += "\n" + _texto_pdf(pdf.content)
        except Exception:
            continue
        time.sleep(0.3)
    if not texto_total.strip():
        resultado["evidencias"]["erro"] = "nenhum texto extraível (PDF digitalizado?)"
        return resultado

    m = RE_NAO_EXIGE.search(texto_total)
    if m:
        resultado["atestado"] = "NAO_EXIGE"
        resultado["evidencias"]["atestado"] = re.sub(r"\s+", " ", m.group(0))[:250]
    else:
        m = RE_EXIGE.search(texto_total)
        if m:
            resultado["atestado"] = "EXIGE"
            i = max(0, m.start() - 80)
            resultado["evidencias"]["atestado"] = re.sub(
                r"\s+", " ", texto_total[i:m.end() + 150])[:250]

    m = RE_MORTO.search(texto_total)
    if m:
        resultado["vida"] = "MORTA"
        i = max(0, m.start() - 80)
        resultado["evidencias"]["vida"] = re.sub(r"\s+", " ", texto_total[i:m.end() + 120])[:250]
    else:
        resultado["vida"] = "VIVA"

    m = RE_SESSAO.search(texto_total)
    if m:
        resultado["data_sessao"] = m.group(1)
        resultado["evidencias"]["sessao"] = re.sub(r"\s+", " ", m.group(0))[:150]

    sinais = {}
    for nome, rx in RE_SINAIS.items():
        ms = rx.search(texto_total)
        if ms:
            i = max(0, ms.start() - 60)
            sinais[nome] = re.sub(r"\s+", " ", texto_total[i:ms.end() + 100])[:150]
    resultado["evidencias"]["sinais"] = sinais
    return resultado


def triar_qualificadas(session: Session, tenant_id: str) -> dict:
    from ..models import FitScore
    fits = session.scalars(select(FitScore).where(
        FitScore.tenant_id == tenant_id, FitScore.decisao_recomendada != "NO_GO")).all()
    stats = {"triadas": 0, "vivas_sem_atestado": 0, "mortas": 0, "exigem": 0, "indefinidas": 0}
    for f in fits:
        if session.scalar(select(Triage).where(Triage.opportunity_id == f.opportunity_id)):
            continue
        opp = session.get(Opportunity, f.opportunity_id)
        r = triar_oportunidade(opp)
        session.add(Triage(opportunity_id=opp.id, atestado=r["atestado"], vida=r["vida"],
                           data_sessao=r["data_sessao"], evidencias=r["evidencias"]))
        stats["triadas"] += 1
        if r["vida"] == "MORTA":
            stats["mortas"] += 1
        elif r["atestado"] == "NAO_EXIGE":
            stats["vivas_sem_atestado"] += 1
        elif r["atestado"] == "EXIGE":
            stats["exigem"] += 1
        else:
            stats["indefinidas"] += 1
    session.add(AuditLog(tenant_id=tenant_id, ator="agents/08_LEITURA_EDITAL", tipo_ator="ia",
                         acao="triagem:concluida", detalhe=stats))
    session.flush()
    return stats
