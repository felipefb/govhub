# Evidência — Conector PNCP (Sprint 02)

- Data: 2026-07-15 | Responsável: Felipe (pendente de revisão)
- Testes unitários: 7/7 passando (mapeamento canônico, dedup idempotente, quarentena, regime jurídico, isolamento de tenant, audit imutável, gate humano).
- Validação ao vivo: API pública do PNCP retornou timeout/504 durante a janela de teste (instabilidade da fonte). O conector tratou corretamente com retry + backoff e erro `FonteIndisponivel` — nenhum dado inventado.
- Pendência: reexecutar validação ao vivo quando o PNCP normalizar e anexar amostra real aqui.
