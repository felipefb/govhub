# GovExperts

**Prioridade:** P2

## Objetivo
Marketplace de especialistas credenciados (assessorias, advogados, contadores, engenheiros).

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- credenciamento com níveis de verificação
- pendência → serviços disponíveis
- comissão transparente e contratual
- gestão de SLA e avaliações

## Entidades mínimas
- `specialist`
- `service_offering`
- `engagement`
- `rating`

## Time de agentes responsável
- `agents/28_SPECIALIST_MARKETPLACE.md`
- `agents/30_SUPPLIER_REPUTATION.md`
- `agents/31_HUMAN_ESCALATION.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
