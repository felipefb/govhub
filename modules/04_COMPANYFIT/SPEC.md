# CompanyFit

**Prioridade:** P0

## Objetivo
Identificar oportunidades adequadas a cada empresa com score de aderência explicável.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- score 0-100 com pesos declarados
- justificativa por componente
- recomendação GO / GO COM CONDIÇÕES / PARCERIA NECESSÁRIA / NO-GO
- condições para participação

## Entidades mínimas
- `company`
- `opportunity`
- `fit_score`
- `requirement`

## Time de agentes responsável
- `agents/07_FIT_COMERCIAL.md`
- `agents/11_CAPABILITY_MATCHER.md`
- `agents/04_INTELIGENCIA_COMPETITIVA.md`
- `agents/10_RISCO_INTEGRIDADE.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
