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
    from datetime import date

    with SessionLocal() as s:
        empresas = s.scalars(select(Company).where(Company.tenant_id == tenant_id)).all()
        hoje = date.today().isoformat()
        opps = s.scalars(select(Opportunity).where(
            Opportunity.status == "aberta",
            (Opportunity.data_limite.is_(None)) | (Opportunity.data_limite >= hoje),
        )).all()
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


def onboarding_bfsa() -> None:
    """Segundo tenant do hub — BFSA Trade Law (Borges Furlaneto & Sayeg Advogados).

    Perfil declarado pelo indicante (Felipe, 2026-07-16): direito aduaneiro e
    comércio internacional. Dados a completar pelo próprio escritório no onboarding
    formal (porte, ticket, regiões, capacidade) — campos ausentes reduzem a
    confiança do score, nunca são presumidos.
    """
    with SessionLocal() as s:
        if not s.scalar(select(Company).where(Company.tenant_id == "bfsa")):
            s.add(Company(
                tenant_id="bfsa", cnpj="33667079000168",
                razao_social="BORGES FURLANETO & SAYEG ADVOGADOS (BFSA Trade Law)",
                cnaes=[], setores=["juridico", "aduaneiro_comex"], uf="SP",
                perfil={"origem": "indicação Felipe/Avintis 2026-07-16; perfil declarado, "
                                  "pendente de onboarding formal"},
            ))
            s.commit()
            print("tenant 'bfsa' criado (perfil declarado)")
    score("bfsa")


def onboarding_avintis() -> None:
    """Perfil real — fonte: Dossiê de Prontidão B2G Avintis (2026-07-15).

    Setores derivados dos CNAEs registrados (6204-0/00, 6201-5/01, 6202-3/00,
    6203-1/00): software e consultoria/dados. 'capacitacao' fica FORA até
    alteração contratual (não há CNAE 8599-6/04).
    ticket_max = ~R$ 385.000: teto de habilitação econômico-financeira
    (PL R$ 38.506,99 × 10, regra do PL ≥ 10% do contrato, Lei 14.133/2021).
    """
    perfil = {
        "completude_documental": 0.6,  # SICAF em validação; certidões nível IV pendentes
        "ticket_min": 10000,           # exceção estratégica p/ formação de acervo sinalizada no score
        "ticket_max": 385000,
        "capital_giro": 0,             # sem caixa próprio: priorizar ciclo curto/parcelado
        "interesse_consorcio": True,
        "interesse_subcontratacao": True,
        "porte": "ME",
        "simples_nacional": True,
        "patrimonio_liquido": 38506.99,
        "indices": {"LC": 2.93, "LG": 9.41, "SG": 9.41},
        "origem": "Dossiê de Prontidão B2G 2026-07-15 (balanço 2025 + RFB + PNCP)",
    }
    with SessionLocal() as s:
        c = s.scalar(select(Company).where(Company.tenant_id == "avintis"))
        if c:
            c.cnpj, c.razao_social, c.uf = "61167552000183", "AVINTIS LTDA", "SP"
            c.cnaes = ["6204-0/00", "6201-5/01", "6202-3/00", "6203-1/00"]
            c.setores = ["software", "dados_analytics", "inteligencia_artificial", "automacao"]
            c.perfil = perfil
        else:
            s.add(Company(
                tenant_id="avintis", cnpj="61167552000183", razao_social="AVINTIS LTDA",
                cnaes=["6204-0/00", "6201-5/01", "6202-3/00", "6203-1/00"],
                setores=["software", "dados_analytics", "inteligencia_artificial", "automacao"],
                uf="SP", perfil=perfil,
            ))
        s.commit()
        print("perfil real da Avintis aplicado (tenant 'avintis')")
    score("avintis")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if cmd == "ingest":
        ingest(sys.argv[2], sys.argv[3])
    elif cmd == "score":
        score(sys.argv[2])
    elif cmd == "verify":
        from .ingestion.verify import verificar_qualificadas
        with SessionLocal() as s:
            print(verificar_qualificadas(s, sys.argv[2]))
            s.commit()
    elif cmd == "triage":
        from .analysis.triage import triar_qualificadas
        with SessionLocal() as s:
            print(triar_qualificadas(s, sys.argv[2]))
            s.commit()
    elif cmd == "daily":
        # rotina diária do Plano A: ingerir ontem+hoje, pontuar, verificar na fonte, triar
        from datetime import date, timedelta

        from .analysis.triage import triar_qualificadas
        from .ingestion.verify import verificar_qualificadas
        hoje, ontem = date.today().isoformat(), (date.today() - timedelta(days=1)).isoformat()
        ingest(ontem, hoje)
        tenant = sys.argv[2] if len(sys.argv) > 2 else "avintis"
        score(tenant)
        with SessionLocal() as s:
            print("verify:", verificar_qualificadas(s, tenant))
            from .ingestion.verify import enriquecer_detalhes
            print("enrich:", enriquecer_detalhes(s, tenant))
            print("triage:", triar_qualificadas(s, tenant))
            s.commit()
    elif cmd == "partners":
        from .analysis.partners import sugerir_parceiros
        with SessionLocal() as s:
            for item in sugerir_parceiros(s, sys.argv[2] if len(sys.argv) > 2 else "avintis"):
                print(f"\n[{item['uf']}] R$ {item['valor'] or 0:,.0f} | {item['objeto'][:90]}")
                for p in item["parceiros"]:
                    print(f"  {p['score']:5.1f} | {p['nome'][:45]} | {p['contratos_recentes']}x")
    elif cmd == "winners":
        from .analysis.winners import coletar, ranking
        with SessionLocal() as s:
            if len(sys.argv) > 3:
                print(coletar(s, sys.argv[2], sys.argv[3]))
                s.commit()
            for i, e in enumerate(ranking(s), 1):
                print(f"{i:2d}. {e['nome'][:45]:45s} {e['contratos']:2d}x R$ {e['valor_total']:>13,.0f} "
                      f"{','.join(e['ufs'])[:15]} {','.join(e['setores'])[:35]}")
    else:
        onboarding_avintis()
