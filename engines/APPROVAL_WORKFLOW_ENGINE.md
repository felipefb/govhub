# Approval Workflow Engine

Máquina de estados: RASCUNHO_IA → REVISAO_ESPECIALISTA → REVISAO_CLIENTE → APROVADO → ENVIADO_PELO_HUMANO. Transições exigem identidade humana autenticada e são gravadas em approval + audit_log. Estados não podem ser pulados. Núcleo do Human-in-the-Loop.
