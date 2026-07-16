"""Pendência #6 — complexidade e risco jurídico alimentados pela triagem documental."""
from govhub.analysis.triage import Triage
from govhub.models import Company, Opportunity
from govhub.scoring.fit import calcular


def _cenario(session, sinais):
    c = Company(tenant_id="t1", cnpj="1", razao_social="X",
                setores=["inteligencia_artificial"], perfil={"completude_documental": 0.9})
    o = Opportunity(fonte="pncp", chave_fonte="k1", orgao="Org", uf="SP",
                    objeto="Contratação de chatbot com inteligência artificial",
                    modalidade="Pregão", data_limite="2099-01-01")
    session.add_all([c, o])
    session.flush()
    session.add(Triage(opportunity_id=o.id, atestado="EXIGE", vida="VIVA",
                       evidencias={"sinais": sinais}))
    session.flush()
    return c, o


def test_sinais_pesados_reduzem_componentes(session):
    c, o = _cenario(session, {"poc_ou_amostra": "prova de conceito presencial",
                              "garantia_exigida": "seguro-garantia de 5%"})
    fs = calcular(session, c, o)
    assert fs.componentes["complexidade_operacional"] == 0.5   # 0.85 - 0.20 - 0.15
    assert fs.componentes["risco_juridico"] == 0.6             # 0.75 - 0.15
    assert any("sinal documental" in r for r in fs.riscos)


def test_triagem_limpa_melhora_componentes(session):
    c, o = _cenario(session, {})
    fs = calcular(session, c, o)
    assert fs.componentes["complexidade_operacional"] == 0.85  # docs lidos, sem sinais
    assert fs.componentes["risco_juridico"] == 0.75
