# Evidência — Conector PNCP (Sprint 02)

- Data: 2026-07-15 | Responsável: Felipe (pendente de revisão)
- Testes unitários: 7/7 passando (mapeamento canônico, dedup idempotente, quarentena, regime jurídico, isolamento de tenant, audit imutável, gate humano).
- Validação ao vivo: API pública do PNCP retornou timeout/504 durante a janela de teste (instabilidade da fonte). O conector tratou corretamente com retry + backoff e erro `FonteIndisponivel` — nenhum dado inventado.
- Pendência: reexecutar validação ao vivo quando o PNCP normalizar e anexar amostra real aqui.

## Atualização — mesma data, mais tarde
- PNCP normalizou: `buscar()` retornou 50 registros reais (janela 2026-07-14→15, pregão eletrônico), todos ingeridos sem quarentena.
- Compras.gov.br (dadosabertos, módulo contratações 14.133): 1.253 registros reais ingeridos em 9 modalidades.
- Fit score sobre 1.303 oportunidades reais: 22 GO + 1 GO_COM_CONDICOES (taxonomia v2 com termos fortes/fracos e fronteira de palavra; antes 103 qualificadas com falsos positivos).
- Cockpit web validado no navegador com esses dados.
- Pendências #1, #2 e #3 fechadas em backlog/PENDENCIAS.md.
