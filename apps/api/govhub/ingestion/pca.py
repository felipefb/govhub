"""GovProjects — demanda antecipada via Planos de Contratações Anuais (agente 02).

Varre as atualizações de PCA no PNCP e captura ITENS DE SERVIÇO aderentes à
taxonomia: são compras que os órgãos PLANEJAM fazer — visibilidade de 3-12 meses
antes do edital. Toda previsão é inferência sobre plano declarado, nunca certeza.
"""
import time

import httpx
from sqlalchemy import Float, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..models import AuditLog, Base
from ..scoring.fit import _norm, setores_do_objeto

PCA_URL = "https://pncp.gov.br/api/consulta/v1/pca/atualizacao"


class PcaDemand(Base):
    __tablename__ = "pca_demand"
    id: Mapped[int] = mapped_column(primary_key=True)
    chave: Mapped[str] = mapped_column(String, unique=True)  # idPcaPncp|numeroItem
    orgao: Mapped[str] = mapped_column(String)
    orgao_cnpj: Mapped[str] = mapped_column(String)
    unidade: Mapped[str | None] = mapped_column(String, nullable=True)
    descricao: Mapped[str] = mapped_column(String)
    valor_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_desejada: Mapped[str | None] = mapped_column(String, nullable=True)
    ano_pca: Mapped[int | None] = mapped_column(nullable=True)
    setores: Mapped[str] = mapped_column(String)  # csv


def coletar_pca(session: Session, data_inicio: str, data_fim: str,
                max_paginas: int = 30, tamanho_pagina: int = 500) -> dict:
    """Datas AAAAMMDD. Persiste apenas itens de SERVIÇO aderentes à taxonomia."""
    pagina, total_paginas = 1, 1
    itens_vistos = capturados = 0
    while pagina <= min(total_paginas, max_paginas):
        try:
            r = httpx.get(PCA_URL, params={"dataInicio": data_inicio, "dataFim": data_fim,
                                           "pagina": pagina, "tamanhoPagina": tamanho_pagina},
                          timeout=120)
            r.raise_for_status()
            d = r.json()
        except Exception:
            time.sleep(3)
            pagina += 1
            continue
        total_paginas = d.get("totalPaginas") or 1
        for reg in d.get("data", []):
            for it in reg.get("itens", []) or []:
                itens_vistos += 1
                if (it.get("categoriaItemPcaNome") or "") != "Serviço":
                    continue
                desc = it.get("descricaoItem") or ""
                setores = setores_do_objeto(_norm(desc))
                if not setores:
                    continue
                chave = f"{reg.get('idPcaPncp')}|{it.get('numeroItem')}"
                if session.scalar(select(PcaDemand).where(PcaDemand.chave == chave)):
                    continue
                session.add(PcaDemand(
                    chave=chave, orgao=reg.get("orgaoEntidadeRazaoSocial") or "",
                    orgao_cnpj=reg.get("orgaoEntidadeCnpj") or "",
                    unidade=(reg.get("nomeUnidade") or "")[:80],
                    descricao=desc[:400], valor_total=it.get("valorTotal"),
                    data_desejada=(it.get("dataDesejada") or "")[:10] or None,
                    ano_pca=reg.get("anoPca"), setores=",".join(sorted(setores)),
                ))
                capturados += 1
        session.flush()
        pagina += 1
        time.sleep(0.3)
    session.add(AuditLog(tenant_id="_plataforma", ator="agents/02_DEMANDA_ANTECIPADA",
                         tipo_ator="ia", acao="pca:coleta",
                         detalhe={"itens_vistos": itens_vistos, "capturados": capturados,
                                  "paginas": min(total_paginas, max_paginas)}))
    session.flush()
    return {"itens_vistos": itens_vistos, "capturados": capturados}


def demanda_futura(session: Session, limit: int = 40) -> list[PcaDemand]:
    return session.scalars(select(PcaDemand)
                           .order_by(PcaDemand.data_desejada.is_(None), PcaDemand.data_desejada)
                           .limit(limit)).all()
