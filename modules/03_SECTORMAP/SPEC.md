# SectorMap

**Prioridade:** P1

## Objetivo
Decompor projetos públicos por setores e cadeia de fornecimento (Radar Multissetorial).

## Usuários
- empresa fornecedora (PME ou enterprise);
- gestor de licitações;
- especialista credenciado (advogado, contador, engenheiro, pricing);
- operador do hub (Avintis);
- administrador da plataforma.

## Capacidades
- taxonomia multissetorial de bens, serviços e obras
- decomposição de projetos em fases e itens
- associação item → setor → empresas compatíveis
- página marketplace por projeto

## Entidades mínimas
- `sector`
- `supply_chain_item`
- `public_project`
- `opportunity`

## Time de agentes responsável
- `agents/05_SECTOR_DISCOVERY.md`
- `agents/06_PROJECT_DECOMPOSER.md`
- `agents/11_CAPABILITY_MATCHER.md`

## Human in the Loop
Toda ação crítica deste módulo segue o fluxo obrigatório: IA → Especialista → Cliente → Aprovação → Envio. O módulo bloqueia avanço sem aprovação registrada em `approval` e `audit_log`.

## Fora de escopo
- criar escopo técnico sem validação de especialista;
- definir preço final;
- assinar ou enviar documentos;
- substituir advogado, contador ou responsável técnico.
