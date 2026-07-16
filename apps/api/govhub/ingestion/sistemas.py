"""Conector Sistema S — sistematransparenciaweb.com.br (SESI/SENAI e regionais).

Fonte fora do PNCP: entidades do Sistema S licitam por regulamento próprio (RCA)
e publicam num SaaS de transparência central com API JSON pública. Regime jurídico
marcado como 'regulamento_proprio' — as regras de habilitação diferem da 14.133
(em geral mais simples: bom para formação de acervo).
"""
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from .core import ingerir

BASE_URL = "https://sistematransparenciaweb.com.br/api-licitacoes/publico/licitacoes"
FONTE = "sistema_s"
# (entidade nacional, departamento regional) — ampliar conforme validação
REGIONAIS = [("SENAI", "SENAI-SP"), ("SESI", "SESI-SP")]
HEADERS = {"User-Agent": "Mozilla/5.0 (GovHub radar)", "accept": "application/json"}


def _data_iso(br: str | None) -> str | None:
    if not br:
        return None
    try:
        return datetime.strptime(br.strip()[:10], "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def mapear(raw: dict) -> dict:
    status_txt = (raw.get("statusLicitacao") or "").lower()
    aberto = "aberto" in status_txt or "execu" in status_txt
    regional = raw.get("entidadeRegional") or raw.get("nmEmpresa") or "SISTEMA_S"
    return {
        "fonte": FONTE,
        "chave_fonte": f"{regional}|{raw.get('numero')}",
        "orgao": f"{regional} (Sistema S)",
        "uf": (regional.split("-")[-1] if "-" in regional else None),
        "municipio": None,
        "objeto": raw.get("objeto") or raw.get("titulo"),
        "modalidade": raw.get("modalidade") or "RCA",
        "regime_juridico": "regulamento_proprio",
        "valor_estimado": None,  # a fonte não publica estimativa — nunca inventar
        "data_limite": _data_iso(raw.get("dataAbertura")),
        "status": "aberta" if aberto else "encerrada",
        "momento_demanda": "oportunidade_aberta",
        "url_fonte": "https://transparencia.sp.senai.br/licitacoes/licitacoes-editais"
        if "SENAI" in regional else "https://transparencia.sesisp.org.br/licitacoes/licitacoes-editais",
    }


def ingerir_sistema_s(session: Session, ano: int | None = None) -> dict:
    ano = ano or datetime.now(timezone.utc).year
    total = {"novos": 0, "atualizados": 0, "quarentena": 0}
    for entidade, depto in REGIONAIS:
        try:
            r = httpx.get(BASE_URL, params={"ano": ano, "departamento": depto,
                                            "entidade": entidade},
                          timeout=90, headers=HEADERS)
            r.raise_for_status()
            regs = r.json()
        except Exception:
            continue
        if not isinstance(regs, list):
            continue
        res = ingerir(session, FONTE, "agents/01_RADAR_CONTRATACOES", mapear, regs)
        for k in total:
            total[k] += res[k]
    return total
