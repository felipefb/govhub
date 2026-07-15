"""Pipeline MVP 1: ingestão de fontes reais → fit score por empresa.

Uso:
    python -m govhub.pipeline ingest 2026-07-14 2026-07-15
    python -m govhub.pipeline score <tenant_id>
    python -m govhub.pipeline demo   # cria empresa exemplo e roda tudo
"""
import sys

from sqlalchemy import select

from .db import make_engine, make_session
from .ingestion import comprasgov, pncp
from .ingestion.core import FonteIndisponivel
from .models import Company, FitScore, Opportunity
from .scoring.fit import calcular

SessionLocal = make_session(make_engine())


def ingest(data_inicial: str, data_final: str) -> None:
    with SessionLocal() as s:
        try:
            r = comprasgov.ingerir_periodo(s, data_inicial, data_final)
            print(f"comprasgov: {r}")
        except FonteIndisponivel as e:
            print(f"comprasgov INDISPONÍVEL: {e}")
        try:
            regs = pncp.buscar(data_inicial.replace("-", ""), data_final.replace("-", ""))
            print(f"pncp: {pncp.ingerir(s, regs)}")
        except FonteIndisponivel as e:
            print(f"pncp INDISPONÍVEL: {e}")
        s.commit()


def score(tenant_id: str) -> None:
    with SessionLocal() as s:
        empresas = s.scalars(select(Company).where(Company.tenant_id == tenant_id)).all()
        opps = s.scalars(select(Opportunity).where(Opportunity.status == "aberta")).all()
        n = 0
        for c in empresas:
            ja = {f.opportunity_id for f in s.scalars(
                select(FitScore).where(FitScore.company_id == c.id))}
            for o in opps:
                if o.id not in ja:
                    calcular(s, c, o)
                    n += 1
        s.commit()
        print(f"{n} scores calculados para tenant {tenant_id}")


def demo() -> None:
    with SessionLocal() as s:
        if not s.scalar(select(Company).where(Company.tenant_id == "avintis")):
            s.add(Company(
                tenant_id="avintis", cnpj="00000000000000", razao_social="Avintis Ltda.",
                setores=["inteligencia_artificial", "dados_analytics", "software",
                         "automacao", "capacitacao"],
                uf="SP",
                perfil={"completude_documental": 0.7, "ticket_max": 300000},
            ))
            s.commit()
            print("empresa demo criada: Avintis (tenant 'avintis')")
    score("avintis")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if cmd == "ingest":
        ingest(sys.argv[2], sys.argv[3])
    elif cmd == "score":
        score(sys.argv[2])
    else:
        demo()
