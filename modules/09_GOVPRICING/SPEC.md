# GovPricing

**Prioridade:** P0

## Objetivo
Formação e validação de orçamento multissetorial com referências públicas rastreáveis.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- estrutura de custos por setor
- pesquisa de preços públicos com fonte e data
- cenários e sensibilidade
- alçada humana de lance (piso absoluto com bloqueio)

## Entidades mínimas
- `cost_component`
- `pricing_scenario`
- `price_reference`
- `approval`

## Time de agentes responsável
- `agents/20_PRICING_ORCAMENTO.md`
- `agents/21_ESTRUTURA_CUSTOS.md`
- `agents/22_PESQUISA_PRECOS.md`
- `agents/23_VALIDACAO_COMERCIAL.md`
- `agents/31_HUMAN_ESCALATION.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
