"""Sprint 03 — testes de aceite: score explicável, confiança, decisão humana pendente."""
from govhub.ingestion.pncp import ingerir
from govhub.models import Company, Opportunity
from govhub.scoring.fit import calcular
from tests.test_pncp import RAW_OK


def _empresa(session, **kw):
    c = Company(tenant_id="t1", cnpj="1", razao_social="Avintis",
                setores=["dados_analytics", "inteligencia_artificial"],
                perfil={"completude_documental": 0.9, "ticket_max": 500000}, **kw)
    session.add(c)
    session.flush()
    return c


def test_score_explicavel_e_rastreavel(session):
    ingerir(session, [RAW_OK])
    opp = session.query(Opportunity).one()
    fs = calcular(session, _empresa(session), opp)
    assert 0 <= fs.score <= 100
    assert fs.componentes["fit_tecnico"] == 1.0  # objeto de BI × empresa de dados
    assert fs.decisao_recomendada in ("GO", "GO_COM_CONDICOES")
    assert fs.modelo and fs.versao and fs.confianca < 1.0  # dados faltantes reduzem confiança
    assert fs.aprovador_humano is None  # decisão de participação é humana


def test_sem_aderencia_vira_no_go(session):
    opp = Opportunity(fonte="pncp", chave_fonte="k2", orgao="Org", uf="SP",
                      objeto="Aquisição de refeições escolares", modalidade="Pregão")
    session.add(opp)
    session.flush()
    fs = calcular(session, _empresa(session), opp)
    assert fs.decisao_recomendada == "NO_GO"
