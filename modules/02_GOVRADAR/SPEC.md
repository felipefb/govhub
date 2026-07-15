# GovRadar

**Prioridade:** P0

## Objetivo
Encontrar contratações abertas e futuras nas fontes oficiais, deduplicadas e classificadas.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- conectores PNCP, Compras.gov.br, Contrata+Brasil, Painel de Compras
- extração de objeto, órgão, modalidade, valor e prazo
- deduplicação e enriquecimento
- classificação por taxonomia e regime jurídico
- alertas

## Entidades mínimas
- `opportunity`
- `procurement_document`
- `government_buyer`
- `source_registry`

## Time de agentes responsável
- `agents/01_RADAR_CONTRATACOES.md`
- `agents/04_INTELIGENCIA_COMPETITIVA.md`
- `agents/33_INGESTION_ENGINEER.md`
- `agents/32_DATA_ARCHITECT.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
