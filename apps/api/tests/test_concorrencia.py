"""Pendência #6b — probabilidade competitiva pela densidade de vencedores."""
from govhub.analysis.winners import WinnerContract
from govhub.models import Company, Opportunity
from govhub.scoring.fit import calcular, resetar_cache_concorrencia


def _base(session, n_fornecedores):
    for i in range(n_fornecedores):
        session.add(WinnerContract(
            numero_controle=f"c{i}", fornecedor_cnpj=f"cnpj{i}", fornecedor_nome=f"F{i}",
            orgao="Org", uf="SP", objeto="ia", valor_global=1000.0,
            setores=["inteligencia_artificial"]))
    c = Company(tenant_id="t1", cnpj="1", razao_social="X",
                setores=["inteligencia_artificial"], perfil={"completude_documental": 0.9})
    o = Opportunity(fonte="pncp", chave_fonte="k9", orgao="Org", uf="SP",
                    objeto="Serviço de chatbot com inteligência artificial",
                    modalidade="Pregão", data_limite="2099-01-01")
    session.add_all([c, o])
    session.flush()
    resetar_cache_concorrencia()
    return c, o


def test_nicho_aumenta_competitiva(session):
    c, o = _base(session, 3)
    fs = calcular(session, c, o)
    assert fs.componentes["probabilidade_competitiva"] == 0.65
    assert any("nicho" in r for r in fs.riscos)


def test_mercado_disputado_reduz(session):
    c, o = _base(session, 40)
    fs = calcular(session, c, o)
    assert fs.componentes["probabilidade_competitiva"] == 0.4
    assert any("disputado" in r for r in fs.riscos)
