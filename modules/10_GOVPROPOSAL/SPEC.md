# GovProposal

**Prioridade:** P0

## Objetivo
Produção de propostas técnicas e comerciais baseadas apenas em evidências reais.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- leitura completa do edital e matriz de requisitos
- matriz de conformidade requisito → evidência
- primeira versão de proposta técnica e comercial
- workflow de aprovação e versionamento

## Entidades mínimas
- `proposal`
- `proposal_version`
- `requirement`
- `compliance_matrix`
- `approval`

## Time de agentes responsável
- `agents/08_LEITURA_EDITAL.md`
- `agents/18_SOLUCAO_TECNICA.md`
- `agents/19_PROPOSTA_COMERCIAL.md`
- `agents/24_PROPOSAL_ASSEMBLY.md`
- `agents/25_QUALITY_ASSURANCE.md`
- `agents/09_JURIDICO_LICITACOES.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
