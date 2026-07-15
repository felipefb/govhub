# ADR 001 — Monólito modular multi-tenant

## Status
Aprovado (2026-07-15)

## Contexto
O GovHub AI precisa atender milhares de empresas simultaneamente, com 12 módulos de produto fortemente inter-relacionados (a mesma oportunidade atravessa radar, fit, docs, pricing, proposta, bid e contrato) e um workflow de aprovação humano transversal.

## Decisão
Monólito modular com fronteiras explícitas por módulo (padrão do agent_team_app, mesmo do EQUIA_OS), banco único multi-tenant com row-level security, filas para ingestão e processamento de documentos, e engines compartilhadas. Extração para serviços somente quando um módulo demonstrar necessidade operacional (ex.: ingestão em alta escala).

## Consequências
- velocidade de entrega do MVP;
- transações consistentes no workflow de aprovação;
- disciplina de fronteiras obrigatória (revisada pelo Orchestrator);
- ingestão é o primeiro candidato a extração futura.
