"""Radar de vencedores (GovPartners) — prospecção de parceiros para subcontratação.

Varre os contratos publicados no PNCP, filtra objetos de TIC pela taxonomia e
agrega por fornecedor vencedor: são as empresas que JÁ TÊM contrato e atestado
e podem subcontratar a Avintis como especialista em IA/dados.

Uso ético: lista de prospecção comercial B2B legítima a partir de dados públicos.
"""
import time

import httpx
from sqlalchemy import JSON, Float, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..models import AuditLog, Base
from ..scoring.fit import _norm, setores_do_objeto

CONTRATOS_URL = "https://pncp.gov.br/api/consulta/v1/contratos"


class WinnerContract(Base):
    __tablename__ = "winner_contract"
    id: Mapped[int] = mapped_column(primary_key=True)
    numero_controle: Mapped[str] = mapped_column(String, unique=True)
    fornecedor_cnpj: Mapped[str] = mapped_column(String, index=True)
    fornecedor_nome: Mapped[str] = mapped_column(String)
    orgao: Mapped[str] = mapped_column(String)
    uf: Mapped[str | None] = mapped_column(String, nullable=True)
    objeto: Mapped[str] = mapped_column(String)
    valor_global: Mapped[float | None] = mapped_column(Float, nullable=True)
    vigencia_fim: Mapped[str | None] = mapped_column(String, nullable=True)
    setores: Mapped[list] = mapped_column(JSON, default=list)
    data_assinatura: Mapped[str | None] = mapped_column(String, nullable=True)


def coletar(session: Session, data_inicial: str, data_final: str,
            max_paginas: int = 200, tamanho_pagina: int = 500) -> dict:
    """Datas AAAAMMDD. Persiste apenas contratos com objeto aderente à taxonomia TIC."""
    pagina, total_paginas = 1, 1
    vistos = tic = 0
    while pagina <= min(total_paginas, max_paginas):
        try:
            r = httpx.get(CONTRATOS_URL, params={
                "dataInicial": data_inicial, "dataFinal": data_final,
                "pagina": pagina, "tamanhoPagina": tamanho_pagina}, timeout=120)
            r.raise_for_status()
            d = r.json()
        except Exception:
            time.sleep(3)
            pagina += 1
            continue
        total_paginas = d.get("totalPaginas") or 1
        for c in d.get("data", []):
            vistos += 1
            objeto = c.get("objetoContrato") or ""
            setores = setores_do_objeto(_norm(objeto))
            if not setores:
                continue
            chave = c.get("numeroControlePncpCompra") or c.get("numeroControlePNCP") or ""
            chave = f"{chave}|{c.get('niFornecedor')}|{c.get('numeroContratoEmpenho', '')}"
            if session.scalar(select(WinnerContract)
                              .where(WinnerContract.numero_controle == chave)):
                continue
            unidade = c.get("unidadeOrgao") or {}
            session.add(WinnerContract(
                numero_controle=chave,
                fornecedor_cnpj=c.get("niFornecedor") or "",
                fornecedor_nome=c.get("nomeRazaoSocialFornecedor") or "",
                orgao=(c.get("orgaoEntidade") or {}).get("razaoSocial") or "",
                uf=unidade.get("ufSigla"),
                objeto=objeto, valor_global=c.get("valorGlobal"),
                vigencia_fim=c.get("dataVigenciaFim"),
                setores=sorted(setores),
                data_assinatura=(c.get("dataAssinatura") or "")[:10] or None,
            ))
            tic += 1
        session.flush()
        pagina += 1
        time.sleep(0.3)
    session.add(AuditLog(tenant_id="_plataforma", ator="agents/27_PARTNER_MATCHING",
                         tipo_ator="ia", acao="winners:coleta",
                         detalhe={"contratos_vistos": vistos, "tic": tic,
                                  "periodo": f"{data_inicial}-{data_final}"}))
    session.flush()
    return {"contratos_vistos": vistos, "tic_persistidos": tic}


def ranking(session: Session, limit: int = 30) -> list[dict]:
    """Agrega vencedores de TIC: candidatos a parceiro/subcontratante."""
    rows = session.scalars(select(WinnerContract)).all()
    por_forn: dict[str, dict] = {}
    for w in rows:
        e = por_forn.setdefault(w.fornecedor_cnpj, {
            "cnpj": w.fornecedor_cnpj, "nome": w.fornecedor_nome, "contratos": 0,
            "valor_total": 0.0, "ufs": set(), "orgaos": set(), "setores": set(),
            "exemplo_objeto": w.objeto[:140]})
        e["contratos"] += 1
        e["valor_total"] += w.valor_global or 0
        e["ufs"].add(w.uf or "?")
        e["orgaos"].add(w.orgao[:40])
        e["setores"].update(w.setores or [])
    out = sorted(por_forn.values(), key=lambda x: -x["valor_total"])[:limit]
    for e in out:
        e["ufs"], e["orgaos"], e["setores"] = sorted(e["ufs"]), sorted(e["orgaos"])[:4], sorted(e["setores"])
    return out
