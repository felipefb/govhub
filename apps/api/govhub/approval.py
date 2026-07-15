"""Approval Workflow Engine — Human in the Loop.

Máquina de estados: RASCUNHO_IA → REVISAO_ESPECIALISTA → REVISAO_CLIENTE →
APROVADO → ENVIADO_PELO_HUMANO. Estados não podem ser pulados; transições
exigem ator humano identificado e são gravadas em audit_log.
"""
from sqlalchemy.orm import Session

from .models import Approval, AuditLog

ESTADOS = [
    "RASCUNHO_IA",
    "REVISAO_ESPECIALISTA",
    "REVISAO_CLIENTE",
    "APROVADO",
    "ENVIADO_PELO_HUMANO",
]


class ApprovalError(Exception):
    pass


def avancar(session: Session, approval: Approval, ator_humano: str, papel: str) -> Approval:
    if not ator_humano or not ator_humano.strip():
        raise ApprovalError("transição exige ator humano identificado")
    idx = ESTADOS.index(approval.estado)
    if idx >= len(ESTADOS) - 1:
        raise ApprovalError("artefato já está no estado final")
    proximo = ESTADOS[idx + 1]
    approval.historico = approval.historico + [
        {"de": approval.estado, "para": proximo, "ator": ator_humano, "papel": papel}
    ]
    approval.estado = proximo
    session.add(AuditLog(
        tenant_id=approval.tenant_id, ator=ator_humano, tipo_ator="humano",
        acao=f"approval:{approval.artefato_tipo}:{proximo}",
        detalhe={"artefato_ref": approval.artefato_ref, "papel": papel},
    ))
    session.flush()
    return approval


def exigir_estado(approval: Approval, estado: str, acao: str) -> None:
    """Gate: bloqueia ação crítica se o artefato não estiver no estado exigido."""
    if approval.estado != estado:
        raise ApprovalError(
            f"ação '{acao}' bloqueada: exige estado {estado}, atual {approval.estado}"
        )
