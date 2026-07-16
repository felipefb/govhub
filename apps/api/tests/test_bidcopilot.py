"""Bid Copilot — matriz de requisitos a partir de texto de edital."""
from govhub.analysis.bidcopilot import montar_matriz
from govhub.models import Company

EDITAL = """
9.1 A habilitação jurídica será comprovada mediante contrato social registrado.
9.2 Prova de regularidade fiscal perante a Fazenda Nacional, FGTS e CNDT.
22.2 Certidão negativa de falência expedida pelo distribuidor da sede.
22.2.h Índices de liquidez iguais ou superiores a 1,0 e patrimônio líquido de 10%.
22.3.c Comprovação de aptidão por meio de atestados de capacidade técnica.
4.8 Será realizada prova de conceito para avaliar a aderência da solução.
"""


def _empresa(session):
    c = Company(tenant_id="t1", cnpj="1", razao_social="X",
                perfil={"patrimonio_liquido": 38506.99, "indices": {"LC": 2.93, "LG": 9.41}})
    session.add(c)
    session.flush()
    return c


def test_matriz_detecta_familias_e_evidencias(session):
    m = montar_matriz(EDITAL, session, _empresa(session))
    ids = {r["id"]: r for r in m}
    assert {"H_JURIDICA", "H_FISCAL", "H_FALENCIA", "H_INDICES", "H_ATESTADO", "T_POC"} <= set(ids)
    assert ids["H_INDICES"]["status"] == "ATENDE" and "38,506.99" in ids["H_INDICES"]["evidencia"]
    assert ids["H_ATESTADO"]["status"] == "GAP"          # honesto: sem acervo ainda
    assert ids["T_POC"]["status"] == "DECISAO_HUMANA"    # nunca decidido pela IA
    assert all(r["trecho"] for r in m)                   # rastreabilidade obrigatória
