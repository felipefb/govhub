# Divergência de fonte — Detran-DF, Dispensa Eletrônica 17/2026 (PNCP 00475855000179-1-000034/2026)

**Resultado: alvo descartado (NO-GO). Caso documentado como evidência de qualidade de dados.**

- O espelho `dadosabertos.compras.gov.br` retornou como objeto: *"solução integrada para o desenvolvimento e orquestração de agentes de inteligência artificial (IA)..."* — o que fez o radar classificar como GO para a Avintis.
- Os documentos oficiais (`docs/aviso_dispensa_17_2026.pdf`, baixado do PNCP em 2026-07-15) e a API de consulta do PNCP mostram o objeto real: **compra de testes psicológicos aprovados pelo CFP e instrumentos neuropsicológicos** (kits Hogrefe) para avaliação de condutores.
- A API de consulta do PNCP para este registro também oscila entre 200 e 500 — registro problemático na própria origem.

## Consequências implementadas
1. `govhub/ingestion/verify.py`: toda oportunidade qualificada (não NO_GO) é reconferida contra a fonte primária (PNCP consulta) antes de ser apresentada; divergência corrige o objeto, invalida o score e registra em audit_log.
2. Correção manual documental deste registro (audit_log `verificacao_pncp:correcao_manual_documental`).
3. Inexigibilidades passam a ser NO_GO automático (fornecedor já definido, sem disputa).

## Aprendizado
A exigência de qualificação técnica deste aviso ("não haverá exigência de qualificação técnica... aquisição de bens sem complexidade") continua sendo o **padrão de certame ideal** para a Avintis formar acervo público — só que com o objeto certo. O radar diário deve caçar dispensas de TI com essa característica.
