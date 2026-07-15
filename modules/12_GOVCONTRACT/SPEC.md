# GovContract

**Prioridade:** P1

## Objetivo
Entrega, medição, pagamento, renovação e atestados após a vitória.

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- acompanhamento de assinatura, garantia e ordem de serviço
- entregas, aceite e medição
- empenho, liquidação e pagamento
- reajuste, renovação, penalidades e atestado final
- alimentação do histórico para novas disputas

## Entidades mínimas
- `contract`
- `deliverable`
- `invoice`
- `payment`
- `risk`

## Time de agentes responsável
- `agents/26_ENTREGA_CONTRATOS.md`
- `agents/23_VALIDACAO_COMERCIAL.md`
- `agents/15_CAPACIDADE_TECNICA.md`
- `agents/31_HUMAN_ESCALATION.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
