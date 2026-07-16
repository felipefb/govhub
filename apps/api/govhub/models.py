"""Modelo canônico mínimo (Sprint 01) — ver data/CANONICAL_MODEL.md."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "company"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    cnpj: Mapped[str] = mapped_column(String)
    razao_social: Mapped[str] = mapped_column(String)
    cnaes: Mapped[list] = mapped_column(JSON, default=list)
    setores: Mapped[list] = mapped_column(JSON, default=list)
    uf: Mapped[str | None] = mapped_column(String, nullable=True)
    perfil: Mapped[dict] = mapped_column(JSON, default=dict)


class Opportunity(Base):
    __tablename__ = "opportunity"
    __table_args__ = (UniqueConstraint("fonte", "chave_fonte", name="uq_fonte_chave"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    fonte: Mapped[str] = mapped_column(String)
    chave_fonte: Mapped[str] = mapped_column(String)  # ex.: numeroControlePNCP
    orgao: Mapped[str] = mapped_column(String)
    uf: Mapped[str | None] = mapped_column(String, nullable=True)
    municipio: Mapped[str | None] = mapped_column(String, nullable=True)
    objeto: Mapped[str] = mapped_column(String)
    modalidade: Mapped[str] = mapped_column(String)
    regime_juridico: Mapped[str] = mapped_column(String, default="lei_14133_2021")
    valor_estimado: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_limite: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="aberta")
    momento_demanda: Mapped[str] = mapped_column(String, default="oportunidade_aberta")
    url_fonte: Mapped[str | None] = mapped_column(String, nullable=True)
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)


class QuarantineRecord(Base):
    """Registros de fonte incompletos: nunca viram oportunidade silenciosamente."""
    __tablename__ = "quarantine"
    id: Mapped[int] = mapped_column(primary_key=True)
    fonte: Mapped[str] = mapped_column(String)
    motivo: Mapped[str] = mapped_column(String)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FitScore(Base):
    __tablename__ = "fit_score"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"))
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunity.id"))
    score: Mapped[float] = mapped_column(Float)
    componentes: Mapped[dict] = mapped_column(JSON, default=dict)
    justificativa: Mapped[str] = mapped_column(String)
    riscos: Mapped[list] = mapped_column(JSON, default=list)
    condicoes: Mapped[list] = mapped_column(JSON, default=list)
    decisao_recomendada: Mapped[str] = mapped_column(String)
    versao: Mapped[str] = mapped_column(String)
    data: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    modelo: Mapped[str] = mapped_column(String)
    versao_prompt: Mapped[str] = mapped_column(String)
    confianca: Mapped[float] = mapped_column(Float)
    aprovador_humano: Mapped[str | None] = mapped_column(String, nullable=True)


class Certificate(Base):
    """Certidões do data room com alerta de vencimento (GovDocs/GovReady)."""
    __tablename__ = "certificate"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    nome: Mapped[str] = mapped_column(String)
    referencia: Mapped[str | None] = mapped_column(String, nullable=True)
    validade: Mapped[str] = mapped_column(String)          # ISO yyyy-mm-dd
    alerta_dias: Mapped[int] = mapped_column(default=15)


class Approval(Base):
    """Artefato crítico sob workflow humano — ver engines/APPROVAL_WORKFLOW_ENGINE.md."""
    __tablename__ = "approval"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    artefato_tipo: Mapped[str] = mapped_column(String)   # proposta, orcamento, lance, declaracao...
    artefato_ref: Mapped[str] = mapped_column(String)
    estado: Mapped[str] = mapped_column(String, default="RASCUNHO_IA")
    historico: Mapped[list] = mapped_column(JSON, default=list)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    quando: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ator: Mapped[str] = mapped_column(String)        # humano identificado ou agente de IA
    tipo_ator: Mapped[str] = mapped_column(String)   # "humano" | "ia"
    acao: Mapped[str] = mapped_column(String)
    detalhe: Mapped[dict] = mapped_column(JSON, default=dict)
