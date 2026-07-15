# GovPartners

**Prioridade:** P2

## Objetivo
Conectar empresas complementares para parcerias, subcontratação e consórcios.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- matching por lacuna de capacidade
- complementaridade de atestados
- workflow de formação de consórcio com revisão jurídica
- divisão de escopo

## Entidades mínimas
- `company`
- `partnership`
- `consortium`
- `technical_evidence`

## Time de agentes responsável
- `agents/27_PARTNER_MATCHING.md`
- `agents/29_CONSORTIUM_BUILDER.md`
- `agents/09_JURIDICO_LICITACOES.md`
- `agents/10_RISCO_INTEGRIDADE.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
