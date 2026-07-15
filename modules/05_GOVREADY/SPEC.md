# GovReady

**Prioridade:** P0

## Objetivo
Avaliar prontidão documental, técnica e financeira da empresa (score 0-100) e plano de adequação.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- score de prontidão com pesos declarados
- diagnóstico de pendências
- recomendação de faixa de valor inicial
- plano de adequação priorizado

## Entidades mínimas
- `company`
- `readiness_score`
- `certificate`
- `technical_evidence`

## Time de agentes responsável
- `agents/12_PROCUREMENT_READINESS.md`
- `agents/17_COMPANY_ONBOARDING.md`
- `agents/15_CAPACIDADE_TECNICA.md`
- `agents/14_DOCUMENTACAO_CERTIDOES.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
