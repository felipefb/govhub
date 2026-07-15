# GovProjects

**Prioridade:** P1

## Objetivo
Identificar programas, obras e projetos públicos antes da publicação de editais.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- monitoramento de PCA, orçamento, convênios e transferências
- detecção de projetos anunciados
- páginas de projeto com oportunidades derivadas
- alertas de demanda futura (3-12 meses)

## Entidades mínimas
- `government_buyer`
- `public_project`
- `opportunity`
- `procurement_document`

## Time de agentes responsável
- `agents/02_DEMANDA_ANTECIPADA.md`
- `agents/05_SECTOR_DISCOVERY.md`
- `agents/06_PROJECT_DECOMPOSER.md`
- `agents/03_INTELIGENCIA_ORGAO.md`
- `agents/33_INGESTION_ENGINEER.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
