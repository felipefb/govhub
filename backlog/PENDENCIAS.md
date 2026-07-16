# Pendências para uso 100% real — GovHub AI

Fonte de verdade das pendências. Nada aqui pode ser esquecido: o objetivo é operar com dados reais de certames.

| # | Pendência | Status | Evidência |
|---|-----------|--------|-----------|
| 5 | Novas fontes: Sistema S SP FEITO (conector API JSON central sistematransparenciaweb, SESI+SENAI-SP, 423 licitações, no daily). Restam: outras regionais do Sistema S (mesma API, só ampliar REGIONAIS), estatais/Petronect, Contrata+Brasil, Painel de Compras | parcialmente fechada | govhub/ingestion/sistemas.py |

| 18 | Radar diário de dispensas de TI sem exigência de qualificação técnica (padrão ideal p/ formar acervo) | aberta | bids/2026_DETRANDF_DE17/DIVERGENCIA.md |


| 7 | Postgres em produção (hoje SQLite dev) + row-level security | aberta | — |

| 9 | Autenticação de usuários no cockpit (hoje tenant via header/query) | aberta | — |
| 10 | SICAF: TODOS os itens executados (Cadesp anexada 2026-07-16). Aguardando apenas o reprocessamento do status 'Possui pendência' do Nível IV pelo sistema | aguardando sistema | data/dataroom/CERTIDOES.md |
| 11 | Certidões: validades registradas com alertas (RFB/PGFN vence 22/09/2026 ← próxima); falta apenas Cadesp inexistência de IE | quase fechada | data/dataroom/CERTIDOES.md |
| 13 | Acervo técnico — PLANO A: formar acervo público via dispensas sem exigência de qualificação técnica. Atestado SPES AI não será solicitado (decisão do representante, 2026-07-15); contrato+NFs ficam no data room como lastro secundário (usar apenas com exigência branda, ciente do risco de diligência) | redirecionada | data/dataroom/2025-07-14_contrato_SPES_AI_assinado.pdf |
| 14 | Custos GovPricing: custo/hora por perfil, alíquota efetiva Simples, overhead (incluir serviço da dívida 2026), margem mínima | parcial (capital_giro=0 já registrado e aplicado ao score) | dossiê §4 |
| 15 | Alçadas do workflow: quem decide GO/NO-GO, valida técnica, aprova preço/lance; advogado e contador de referência | aberta | dossiê §5 |
| 16 | Se "capacitação" for alvo real: alteração contratual p/ CNAE 8599-6/04 (hoje setor excluído do perfil) | aberta | dossiê §1 |

Regra: ao fechar uma pendência, mover para a tabela abaixo com data e evidência.

## Fechadas

| # | Pendência | Data | Evidência |
|---|-----------|------|-----------|
| 6b | Probabilidade competitiva pela densidade de vencedores por setor (base de 1.264 contratos), combinada ao benefício ME/EPP | 2026-07-16 | fit.concorrencia_por_setor; 2 testes |
| 6 | Complexidade operacional e risco jurídico alimentados pela triagem documental: 7 sinais (garantia, POC, vistoria, SLA, cessão de PI, subcontratação/consórcio vedados) com trecho-evidência; taxonomia refinada pelo filtro de executabilidade | 2026-07-16 | triage.RE_SINAIS + fit.calcular; 2 testes novos |
| 17 | Verify automático após todo scoring | 2026-07-16 | pipeline.score(auto_verify=True) |
| — | MVP 2 núcleo: Bid Copilot (matriz+checklist+proposta) com botão no cockpit; GovPricing (1.264 contratos de referência, seção de orçamento no pacote de bid); GovProjects (conector PCA de demanda futura no daily + seção no cockpit) | 2026-07-16 | analysis/bidcopilot.py, precos.py; ingestion/pca.py |
| — | Cockpit v2: alertas de certidões (badge por dias restantes) e UI do workflow de aprovação (chips de etapa + formulário com ator humano), validado ponta a ponta | 2026-07-16 | govhub/main.py; teste test_cockpit.py; approval 1 avançou p/ REVISAO_ESPECIALISTA via UI |
| 8 | Ingestão agendada diária (07:30, Task Scheduler: ingest→score→verify→triage) | 2026-07-15 | apps/api/govhub_daily.bat; tarefa "GovHub Radar Diario" |
| 19+20 | Triagem documental automática: exigência de atestado, certame morto (sem disputa/homologado) e data de sessão, com trecho-evidência | 2026-07-15 | govhub/analysis/triage.py; comando pipeline triage |
| — | Verificação de qualificadas contra fonte primária (caso Detran-DF: objeto trocado no espelho dados abertos) | 2026-07-15 | govhub/ingestion/verify.py + bids/2026_DETRANDF_DE17/DIVERGENCIA.md; funil verificado: 3 qualificadas reais |
| 1 | Validação ao vivo do conector PNCP | 2026-07-15 | 50 registros reais ingeridos; validation/evidence/2026-07-15_pncp_connector.md |
| 2 | Conector Compras.gov.br (dados abertos) | 2026-07-15 | 1.253 registros reais ingeridos; govhub/ingestion/comprasgov.py |
| 3 | Cockpit web navegável com dados reais | 2026-07-15 | http://localhost:8777 — 1.303 oportunidades reais |
| 12 | Ticket mínimo R$ 10k (exceção p/ acervo), consórcio e subcontratação: SIM; capital_giro=0 com regra de ciclo de caixa no score | 2026-07-15 | pipeline.onboarding_avintis() + scoring/fit.py |
| 4 | Onboarding com dados reais da Avintis | 2026-07-15 | Dossiê de Prontidão B2G aplicado: CNPJ 61.167.552/0001-83, ME/Simples, 4 CNAEs de TI, ticket_max R$ 385k (PL×10), índices LC 2,93/LG 9,41; `pipeline.onboarding_avintis()`. Radar real: 7 GO, todas ≤ R$ 80k com benefício ME/EPP |
