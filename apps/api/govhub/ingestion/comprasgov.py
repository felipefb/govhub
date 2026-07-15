"""Conector Compras.gov.br — API de Dados Abertos (módulo contratações PNCP/14.133).

Docs: https://dadosabertos.compras.gov.br/v3/api-docs
Restrições da API: datas AAAA-MM-DD; tamanhoPagina entre 10 e 500; codigoModalidade obrigatório.
"""
from sqlalchemy.orm import Session

from .core import classificar_regime, get_com_retry, ingerir

BASE_URL = ("https://dadosabertos.compras.gov.br/"
            "modulo-contratacoes/1_consultarContratacoes_PNCP_14133")
FONTE = "comprasgov"

# codigoModalidade da API: 6=dispensa, 5=pregão... consultar catálogo oficial por modalidade
MODALIDADES_MVP = [1, 2, 3, 4, 5, 6, 7, 8, 9]


def mapear(raw: dict) -> dict:
    situacao = (raw.get("situacaoCompraNomePncp") or "").lower()
    return {
        "fonte": FONTE,
        "chave_fonte": raw.get("numeroControlePNCP"),
        "orgao": raw.get("orgaoEntidadeRazaoSocial"),
        "uf": raw.get("unidadeOrgaoUfSigla"),
        "municipio": raw.get("unidadeOrgaoMunicipioNome"),
        "objeto": raw.get("objetoCompra"),
        "modalidade": raw.get("modalidadeNome"),
        "regime_juridico": classificar_regime(raw.get("amparoLegalNome")),
        "valor_estimado": raw.get("valorTotalEstimado"),
        "data_limite": (raw.get("dataEncerramentoPropostaPncp") or "")[:10] or None,
        "status": "encerrada" if "encerrad" in situacao or "homolog" in situacao else "aberta",
        "momento_demanda": "oportunidade_aberta",
        "url_fonte": f"https://pncp.gov.br/app/editais?q={raw.get('numeroControlePNCP', '')}",
    }


def buscar(data_inicial: str, data_final: str, modalidade: int, pagina: int = 1,
           tamanho_pagina: int = 100) -> tuple[list[dict], int]:
    """Retorna (registros, total_paginas). Datas em AAAA-MM-DD."""
    r = get_com_retry(BASE_URL, {
        "dataPublicacaoPncpInicial": data_inicial, "dataPublicacaoPncpFinal": data_final,
        "codigoModalidade": modalidade, "pagina": pagina,
        "tamanhoPagina": max(10, min(tamanho_pagina, 500)),
    }, timeout=120)
    d = r.json()
    return d.get("resultado") or [], d.get("totalPaginas") or 0


def ingerir_periodo(session: Session, data_inicial: str, data_final: str,
                    modalidades: list[int] | None = None, max_paginas: int = 5) -> dict:
    total = {"novos": 0, "atualizados": 0, "quarentena": 0}
    for mod in modalidades or MODALIDADES_MVP:
        pagina, paginas = 1, 1
        while pagina <= min(paginas, max_paginas):
            regs, paginas = buscar(data_inicial, data_final, mod, pagina)
            if not regs:
                break
            r = ingerir(session, FONTE, "agents/01_RADAR_CONTRATACOES", mapear, regs)
            for k in total:
                total[k] += r[k]
            pagina += 1
    return total
