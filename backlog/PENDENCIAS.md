# Pendências para uso 100% real — GovHub AI

Fonte de verdade das pendências. Nada aqui pode ser esquecido: o objetivo é operar com dados reais de certames.

| # | Pendência | Status | Evidência |
|---|-----------|--------|-----------|
| 4 | Onboarding com dados reais da Avintis (CNAEs, perfil, ticket) — hoje empresa demo | aberta | govhub/pipeline.py `demo()` |
| 5 | Conector Contrata+Brasil e Painel de Compras | aberta | — |
| 6 | Componentes do fit score hoje neutros (competitiva, complexidade, risco jurídico) alimentados pelos agentes 04/08/09; refinar taxonomia (falso positivo residual: "saneantes domissanitários" via termo "capacitação") | aberta | — |
| 7 | Postgres em produção (hoje SQLite dev) + row-level security | aberta | — |
| 8 | Agendamento recorrente da ingestão (hoje CLI manual) | aberta | — |
| 9 | Autenticação de usuários no cockpit (hoje tenant via header/query) | aberta | — |

Regra: ao fechar uma pendência, mover para a tabela abaixo com data e evidência.

## Fechadas

| # | Pendência | Data | Evidência |
|---|-----------|------|-----------|
| 1 | Validação ao vivo do conector PNCP | 2026-07-15 | 50 registros reais ingeridos; validation/evidence/2026-07-15_pncp_connector.md |
| 2 | Conector Compras.gov.br (dados abertos) | 2026-07-15 | 1.253 registros reais ingeridos; govhub/ingestion/comprasgov.py |
| 3 | Cockpit web navegável com dados reais | 2026-07-15 | http://localhost:8777 — 1.303 oportunidades, 23 qualificadas, pipeline R$ 6,3 mi |
