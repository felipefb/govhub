# GovBid

**Prioridade:** P1

## Objetivo
Gestão da participação: prazos, sessões, esclarecimentos, impugnações e recursos (sempre com aprovação humana).

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- calendário de prazos por certame
- preparação de minutas para revisão humana
- registro de sessões e lances com alçada
- acompanhamento de habilitação

## Entidades mínimas
- `bid_session`
- `deadline`
- `legal_document`
- `approval`
- `audit_log`

## Time de agentes responsável
- `agents/09_JURIDICO_LICITACOES.md`
- `agents/16_REGISTRATION_NAVIGATOR.md`
- `agents/31_HUMAN_ESCALATION.md`
- `agents/01_RADAR_CONTRATACOES.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
