# GovHub AI — Avintis GovTech Sales Intelligence OS

Versão inicial: 2026-07-15

Repositório mestre para construir, validar e comercializar uma plataforma SaaS de inteligência comercial para oportunidades públicas e privadas no Brasil. O sistema identifica demandas (futuras, abertas e de expansão contratual), avalia aderência, organiza habilitação, estrutura proposta e orçamento e acompanha a contratação até o pagamento — sempre como **copiloto**, nunca como decisor.

## Regra central

A IA prepara, verifica e recomenda. O representante autorizado decide, declara, assina e assume a obrigação.

Nenhuma ação crítica ocorre sem o fluxo: **IA → Especialista → Cliente → Aprovação → Envio**.

A plataforma NÃO: cria escopo técnico, define preço, assina documentos, envia propostas, declara capacidades inexistentes, nem substitui advogado, contador ou responsável técnico.

## Ordem de execução

1. Leia `START_PROMPT.md`.
2. Leia `docs/PRODUCT_MASTER.md`, `docs/ARCHITECTURE.md` e `governance/DECISION_LOG.md`.
3. Execute `sprints/SPRINT_00_REPOSITORY_AUDIT.md`.
4. Implemente apenas o primeiro vertical slice aprovado (GovRadar + CompanyFit).
5. Registre decisões em ADRs e evidências em `validation/evidence/`.

## MVP comercial prioritário

**GovRadar + CompanyFit + GovReady** (MVP 1 — Radar e qualificação): monitorar PNCP/Compras.gov.br, selecionar dez oportunidades aderentes por mês e apresentar de duas a quatro propostas qualificadas.

## Estrutura

- `agents/`: prompts operacionais dos 40 agentes (6 squads), no padrão agent_team_app.
- `modules/`: especificações dos 12 módulos, cada um com seu time de agentes.
- `data/`: fontes, contratos, qualidade e modelo canônico.
- `engines/`: motores compartilhados de dados e IA.
- `architecture/`: decisões e diagramas.
- `governance/`: decision log, riscos e política Human-in-the-Loop.
- `validation/`: protocolos de teste real.
- `sprints/`: plano de construção.
- `schemas/`: contratos JSON.
- `backlog/`: backlog priorizado.
