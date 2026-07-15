# GovHub AI — Arquitetura

## Estilo
Monólito modular multi-tenant (ver `architecture/ADR_001_MODULAR_MONOLITH.md`), com módulos correspondendo aos 12 domínios de produto e engines compartilhadas.

## Camadas
1. **Ingestão:** conectores idempotentes (PNCP, Compras.gov.br, Contrata+Brasil, Painel de Compras, diários oficiais, portais estaduais/municipais). Deduplicação, quarentena e classificação de regime jurídico.
2. **Modelo canônico:** entidades em `data/CANONICAL_MODEL.md`; linhagem e versionamento obrigatórios.
3. **Engines:** matching, scoring, leitura de documentos, pricing, evidência, workflow de aprovação.
4. **Módulos de produto:** GovProjects … GovContract.
5. **Experiência:** cockpit, marketplace, página de oportunidade, data room, workflows.

## Requisitos transversais
- multi-tenant com isolamento forte por empresa;
- RBAC + segregação de funções;
- audit_log imutável (toda decisão, lance e aprovação);
- rastreabilidade de IA: fonte, documento, trecho, data, modelo, versão do prompt, confiança, aprovador;
- LGPD by design; nenhum armazenamento de certificado digital para uso autônomo;
- escalabilidade horizontal de ingestão e filas para milhares de tenants.

## Workflow de aprovação (núcleo do sistema)
Máquina de estados por artefato crítico: RASCUNHO_IA → REVISAO_ESPECIALISTA → REVISAO_CLIENTE → APROVADO → ENVIADO_PELO_HUMANO. Transições registradas em `approval` e `audit_log`; nenhum estado pode ser pulado.
