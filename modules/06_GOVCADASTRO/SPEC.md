# GovCadastro

**Prioridade:** P1

## Objetivo
Auxiliar cadastros e habilitações (SICAF, portais estaduais/municipais) sem executar atos legais.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- inventário de portais por empresa
- preparação de formulários e rascunhos
- data room com alertas de validade
- acompanhamento de pendências e histórico de submissões

## Entidades mínimas
- `supplier_registration`
- `certificate`
- `procuration`
- `portal`

## Time de agentes responsável
- `agents/13_CADASTRO_FORNECEDOR.md`
- `agents/14_DOCUMENTACAO_CERTIDOES.md`
- `agents/16_REGISTRATION_NAVIGATOR.md`
- `agents/39_SECURITY_LGPD.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
