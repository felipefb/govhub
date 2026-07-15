# Análise de Edital — Pregão Eletrônico 90004/2026 (nº 15/2026) CAU/SC

**Estado do artefato: RASCUNHO_IA — pendente de revisão de especialista e decisão do cliente.**
Gerado por: agents/08_LEITURA_EDITAL | Modelo: leitura assistida por IA generativa | Data: 2026-07-15
Fontes: edital 5/2026.pdf, TR 90004-2026.pdf, Anexo POC (SEI 1018092), baixados do PNCP em 2026-07-15 (`docs/`).

## Resumo do certame

| Campo | Valor | Fonte |
|---|---|---|
| Objeto | Desenvolvimento, configuração e integração de IA (LLM/RAG), licenças e consultoria continuada por 12 meses para atendimento automatizado via WhatsApp | Edital, item 1 |
| Órgão | CAU/SC (UASG 926307) — Florianópolis/SC | Edital |
| Modalidade | Pregão Eletrônico, Lei 14.133/2021 | Edital |
| Valor estimado | R$ 37.108,20 (12 meses) | PNCP |
| Encerramento propostas | 2026-07-30 | PNCP |
| ME/EPP | Tratamento favorecido LC 123/2006 (item 3.8) | Edital |
| Regime | Serviço continuado sem dedicação exclusiva de mão de obra | Edital, cabeçalho |

## Matriz de requisitos de habilitação (requisito → evidência Avintis → status)

| # | Requisito | Fonte | Evidência Avintis | Status |
|---|---|---|---|---|
| H1 | Regularidade fiscal federal/estadual/municipal, FGTS, CNDT (via SICAF) | Edital §9 | SICAF em validação (pendências #10/#11) | ⚠️ EM ANDAMENTO |
| H2 | Certidão negativa de falência | TR 22.2.b | Emitir no TJSP (rápido, gratuito) | ⚠️ EMITIR |
| H3 | Índices econômicos ≥ exigido; PL ≥ 10% do valor (≈ R$ 3.711) | TR 22.2 | PL R$ 38.506,99; LC 2,93; LG/SG 9,41 — folga de 10× | ✅ ATENDE |
| H4 | Declaração dos índices assinada por profissional contábil | TR 22.2.j | Solicitar à Contabilizei | ⚠️ SOLICITAR |
| H5 | Empresa criada recentemente pode usar balanço de abertura (art. 65 §1º) | TR 22.2.i | Avintis tem balanço fechado 2025 — melhor que o mínimo | ✅ ATENDE |
| H6 | Declaração de conhecimento das condições (pode ser do responsável técnico) | TR 22.3.a/b | Felipe assina | ✅ ATENDE |
| H7 | **Atestado de capacidade técnica**: aptidão em serviço de complexidade equivalente/superior, emitido por PJ de direito **público ou privado**; soma de atestados admitida | TR 22.3.c/d | **ZERO atestados formais hoje** — gap crítico. Atestado privado serve: cliente privado de projeto de IA/chatbot/software pode emitir | ❌ GAP — AÇÃO URGENTE |
| H8 | Declarações de praxe (reserva PCD, trabalho de menor, LC 123) | Edital 9.7-9.8 | Declarações no sistema pelo representante | ✅ ATENDE |

## Requisitos técnicos e de execução

| # | Requisito | Fonte | Avaliação |
|---|---|---|---|
| T1 | Chatbot WhatsApp com LLM/RAG, base de conhecimento homologada, sem interpretações jurídicas próprias/especulação | TR 4.x + POC | Núcleo da competência Avintis ✅ |
| T2 | Painel administrativo em tempo real (atendimentos, usuários simultâneos, assuntos, TMA, taxa de transbordo, satisfação) | Anexo POC | Esforço de desenvolvimento médio |
| T3 | Transbordo para atendimento humano + abertura de chamados com protocolo | Anexo POC | Padrão de mercado ✅ |
| T4 | Exportação de relatórios XLS/CSV/TXT/XML | Anexo POC | Simples ✅ |
| T5 | 24/7 com parâmetros distintos comercial/não comercial | Anexo POC | Simples ✅ |
| T6 | **Prova de conceito PRESENCIAL em Florianópolis**: até 5 dias úteis nas dependências do CAU/SC (suporte remoto permitido) + ferramenta em pleno funcionamento para testes por 10 dias | TR 4.8 + Anexo POC | ⚠️ Exige solução JÁ FUNCIONAL antes da contratação + deslocamento SP→Floripa. Custo estimado de POC: viagem + 5 dias + infra ≈ R$ 3-5 mil do próprio bolso, ANTES de receber |
| T7 | Cessão de propriedade intelectual dos artefatos à Administração | TR 5.h | Aceitável para projeto sob encomenda; atenção para não ceder plataforma-base própria — **revisão jurídica** |
| T8 | Manter equipe habilitada durante execução; 12 meses de consultoria continuada | TR 5.f | Compatível com operação solo + faturamento mensal (bom para caixa) |

## Riscos principais

1. **H7 (atestado)** — risco de inabilitação. Mitigações possíveis, em ordem: (a) obter atestado de cliente privado de projeto de IA/software já executado (dossiê §3 diz que a experiência privada existe mas não está documentada — é EXATAMENTE isso que falta); (b) verificar se o pregoeiro aceita comprovação alternativa; (c) não participar e usar o edital como molde para preparar o próximo.
2. **T6 (POC presencial + solução funcionando)** — a Avintis precisaria ter o chatbot essencialmente pronto ~10 dias após a sessão, com custo de viagem antecipado. Sem capital de giro, esse custo (R$ 3-5 mil) precisa de fonte definida ANTES de dar lance.
3. **Prazo**: 15 dias até 30/07 — apertado para fechar SICAF + certidões + atestado.
4. **Concorrência**: plataformas de chatbot estabelecidas podem dar lances agressivos; o valor (R$ 3.092/mês) é baixo para 12 meses de licença+consultoria — margem apertada.

## Recomendação da IA (não é decisão)

**GO COM CONDIÇÕES**, condicionado a TRÊS confirmações humanas até 2026-07-22:
1. Existe cliente privado disposto a emitir atestado de projeto de IA/software equivalente? (sem isso → NO-GO)
2. Há fonte para os ~R$ 3-5 mil da POC presencial? (sem isso → NO-GO)
3. SICAF + certidões fecham a tempo? (Contabilizei consegue a declaração de índices em dias?)

Se qualquer resposta for "não": usar este edital como template de preparação e mirar o próximo (o radar mostra 5 outros GOs com prazos posteriores).

## Checklist documental para participação

- [ ] SICAF níveis validados (pendência #10)
- [ ] Certidões fiscais SP vigentes (pendência #11)
- [ ] Certidão negativa de falência (TJSP)
- [ ] Declaração de índices por contador (Contabilizei)
- [ ] Atestado de capacidade técnica privado (pendência #13 — CRÍTICO)
- [ ] Declaração de conhecimento das condições (Felipe)
- [ ] Proposta de preços conforme modelo do edital
- [ ] Definição humana de alçada de lance (preço inicial / alvo / piso — pendência #15)
