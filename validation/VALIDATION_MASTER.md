# Protocolo de validação — GovHub AI

1. Toda extração de edital é validada contra o documento original (amostragem mínima de 10% por fonte).
2. Todo score é reproduzível a partir do snapshot identificado (dados + modelo + versão do prompt).
3. Backtest temporal: nenhuma avaliação usa informação publicada depois da data de corte.
4. Gate humano testado: nenhuma ação crítica executável sem `approval` registrada.
5. Evidências em `validation/evidence/` com fonte, data e responsável.
6. Revisão de especialista humano (advogado, contador, pricing) antes de qualquer artefato usado em certame real.
