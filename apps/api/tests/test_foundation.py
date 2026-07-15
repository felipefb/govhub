"""Sprint 01 — testes de aceite: isolamento de tenant, audit imutável, gate humano."""
import pytest
from sqlalchemy import select, update

from govhub.approval import ESTADOS, ApprovalError, avancar, exigir_estado
from govhub.models import Approval, AuditLog, Company, FitScore


def test_isolamento_tenant(session):
    session.add_all([
        Company(tenant_id="t1", cnpj="1", razao_social="A"),
        Company(tenant_id="t2", cnpj="2", razao_social="B"),
    ])
    session.flush()
    vistos = session.scalars(select(Company).where(Company.tenant_id == "t1")).all()
    assert [c.razao_social for c in vistos] == ["A"]


def test_audit_log_imutavel(session):
    session.add(AuditLog(tenant_id="t1", ator="x", tipo_ator="humano", acao="teste"))
    session.commit()
    with pytest.raises(Exception, match="imutável"):
        session.execute(update(AuditLog).values(acao="adulterado"))
        session.commit()


def test_workflow_nao_pula_etapas_e_exige_humano(session):
    ap = Approval(tenant_id="t1", artefato_tipo="proposta", artefato_ref="p1")
    session.add(ap)
    session.flush()

    with pytest.raises(ApprovalError):
        avancar(session, ap, "", "especialista")  # sem humano identificado

    with pytest.raises(ApprovalError):
        exigir_estado(ap, "APROVADO", "enviar_proposta")  # gate bloqueia envio

    for papel in ["especialista", "cliente", "cliente", "representante_legal"]:
        avancar(session, ap, "maria@empresa.com", papel)
    assert ap.estado == ESTADOS[-1]
    assert len(ap.historico) == 4

    with pytest.raises(ApprovalError):
        avancar(session, ap, "maria@empresa.com", "cliente")  # estado final

    trilha = session.scalars(select(AuditLog)).all()
    assert len(trilha) == 4 and all(a.tipo_ator == "humano" for a in trilha)
