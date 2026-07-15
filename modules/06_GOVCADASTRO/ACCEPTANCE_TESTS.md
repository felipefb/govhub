# Testes de aceite — GovCadastro

1. O sistema nunca usa certificado digital nem aceita declarações legais autonomamente.
2. Todo envio a portal exige ação do representante legal registrada no audit_log.
3. Alerta de vencimento de certidão deve disparar antes do prazo configurado.
4. Divergência entre documentos deve gerar pendência, não correção silenciosa.
5. Registro com fonte ausente deve ser rejeitado ou colocado em quarentena.
6. Toda saída de IA deve guardar fonte, documento, trecho, data, modelo, versão do prompt, confiança e aprovador.
7. Usuários de tenants diferentes não podem acessar os mesmos artefatos privados.
8. Ação crítica sem aprovação humana registrada deve ser bloqueada.
