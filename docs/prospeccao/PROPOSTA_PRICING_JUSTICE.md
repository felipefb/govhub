# Estrutura de proposta comercial — Avintis → Justice AI

**RASCUNHO_IA — preços são cenários com premissas declaradas; a decisão de preço é humana.**
Preparado em 2026-07-16. Base: contratos públicos da Justice (PNCP) + referência de mercado da
Avintis (contrato privado vigente de R$ 31.000/mês por dedicação principal, desde 07/2025).

## 1. Piso econômico da Avintis (preço mínimo sustentável)

Fórmula GovPricing com premissas A CONFIRMAR (pendência #14):

| Componente | Premissa | R$/mês |
|---|---|---:|
| Remuneração-alvo do sócio (pró-labore + retirada) | a confirmar | 15.000 |
| Tributos (Simples Nacional — anexo III/V depende do Fator R; **confirmar alíquota efetiva com a Contabilizei**) | ~10% da receita | variável |
| Infra e ferramentas (Azure, APIs de LLM, licenças) | estimado | 1.500 |
| Serviço da dívida 2026 + overhead administrativo | do balancete | 2.500 |
| Reserva p/ capital de giro (meta: 2 meses de custo em 12 meses) | disciplina | 2.000 |
| **Custo-base mensal (dedicação integral)** | | **~21.000 + tributos** |

Piso de dedicação integral ≈ **R$ 24-25k/mês** (custo + tributos, margem zero).
Referência de mercado já validada: **R$ 31k/mês** (SPES) → margem ~25% sobre o piso. Coerente.

**Hora-base derivada:** R$ 31k ÷ 140h úteis ≈ **R$ 220/h** (piso absoluto ≈ R$ 175/h).

## 2. O que a Justice precisa (dos contratos públicos deles)

- **TJ-PI (R$ 1,41M/12m)**: inclui *fornecimento de infraestrutura* — implantação, integrações,
  ambientes, SLA. É o contrato que mais demanda engenharia contínua.
- **Goiás (R$ 1M/12m)**: subscrição SaaS — escala de plataforma, multi-tenant, disponibilidade.
- **Menores (Diadema, SE, SC)**: implantação leve e suporte.

Encargo técnico estimado dos 5 contratos: 1 a 2 engenheiros sênior contínuos + picos de implantação.
Receita mensalizada da carteira deles ≈ R$ 205k/mês. Uma parceria técnica de R$ 15-25k/mês
representa **7-12% da receita da carteira** — faixa saudável de custo de entrega para SaaS
(referência de mercado: custo de delivery/infra em SaaS B2G costuma caber em 20-35% da receita;
proposta bem abaixo disso não pressiona a margem deles).

## 3. Os três modelos a ofertar (em ordem de preferência da Avintis)

### Modelo A — Retainer mensal (recomendado para começar)
- **80h/mês por R$ 16.800** (R$ 210/h) — banco de horas com rollover de 20%;
- Escopo: desenvolvimento, integrações, infra de IA dos contratos vigentes;
- Piso de alçada: não aceitar abaixo de R$ 14.000 (R$ 175/h) sem revisão do sócio;
- Para a Justice: custo fixo previsível = 8% da carteira; sem encargo trabalhista, sem banco de talento.

### Modelo B — Por projeto/marco (para implantações)
- Ex.: implantação TJ-PI (infra + integrações): escopo fechado com marcos e aceite;
- Precificação: horas estimadas × R$ 220/h × contingência 20%;
- Pagamento por marco aceito (alinha com o fluxo de recebimento deles junto ao órgão).

### Modelo C — Percentual do contrato (para contratos novos ganhos juntos)
- Avintis como responsável técnica de novos certames que a Justice vencer: **25-30% do valor
  do contrato** pela parcela de engenharia (referência: sub técnico em contratos de software);
- Só para contratos futuros em que a Avintis participe do dimensionamento antes da proposta.

## 4. Contrapartidas não financeiras (inegociáveis — valem mais que preço)
1. Atestado de capacidade técnica por entrega aceita;
2. Subcontratação formalizada perante o órgão quando o contrato permitir;
3. Direito de referência ao projeto.
**Racional declarável ao René:** o preço está abaixo do teto de mercado justamente porque parte
do valor para a Avintis é o acervo. Troca explícita e justa: margem moderada por lastro formal.

## 5. Condições de pagamento (proteção do caixa da Avintis)
- Retainer: faturamento mensal, pagamento até dia 10 do mês seguinte (espelha o padrão SPES);
- Projetos: 30% na largada do marco, 70% no aceite;
- Reajuste anual por IPCA; multa e juros padrão por atraso.

## 6. O que falta o Felipe confirmar antes de enviar (fecha a pendência #14)
- [ ] Remuneração-alvo mensal real;
- [ ] Alíquota efetiva do Simples com a Contabilizei (anexo III vs V — Fator R);
- [ ] Horas/mês disponíveis de verdade (o retainer não pode canibalizar as disputas próprias do Plano A);
- [ ] Aprovação humana dos valores: preço de tabela, preço-alvo e piso absoluto por modelo.
