# Checklist de Visita Técnica — UPA — Instituto Social de Saúde São Lucas

Streamlit + Google Sheets (dados) + Google Drive (evidências). Abre no navegador e no celular.
Mesmo layout do app V03, adaptado ao formulário de UPA (11 seções, 107 itens: 49 essenciais e 58 complementares).

## Rodar local (modo teste, sem Google)
    pip install -r requirements.txt
    streamlit run app.py
Sem credenciais, grava em `dados_locais/Checklist_visita_tecnica_UPA.xlsx` e `evidencias_locais/`.

## Configurar produção
1. Planilha própria **Checklist_visita_tecnica_UPA** (já criada na pasta de planilhas do Drive; ID em `config/mapeamento_visita_tecnica.json`). As abas `UPA_Visitas`, `UPA_Itens`, `UPA_Secoes`, `UPA_Evidencias` e `UPA_Rascunho` são criadas sozinhas no primeiro uso. As pastas do Drive são as mesmas do app V03; os arquivos de planilha são diferentes.
2. A conta de serviço precisa ter acesso de Editor à planilha (herdado da pasta ou compartilhado direto).
3. As fotos vão para a pasta de evidências por um **Web App do Google Apps Script** (`[upload_drive]` nos Secrets: `url` e `token`), o mesmo do app V03 pode ser reutilizado. Cada visita cria uma subpasta com o código `UPA-...`.
4. Publique no Streamlit Community Cloud (HTTPS é necessário para a câmera) e cole os Secrets em *Settings → Secrets*. O app deve ficar público para os visitantes acessarem.

Exemplo de Secrets:
    [gcp_service_account]
    # ... mesmo bloco dos outros apps ...
    [upload_drive]
    url = "https://script.google.com/macros/s/XXXX/exec"
    token = "..."

## Como o formulário foi adaptado
- Cada item tem: Foco (Essencial/Complementar), **Resposta / valor** (com a unidade sugerida quando existe), **Fonte** (Observado, Informado, Observado e informado, Não verificado, Não se aplica), Observação e fotos/PDF.
- "Verificado (OK)" é calculado: tem resposta e a fonte é Observado/Informado/Observado e informado.
- Item respondido = tem resposta, ou foi marcado Não verificado / Não se aplica.
- Cada seção tem um campo "Impacto na proposta e providências São Lucas" (aba `UPA_Secoes`).
- Chave "Mostrar só os itens essenciais" para visita rápida; o menu mostra o progresso de essenciais e complementares.
- O envio completo exige as 11 seções concluídas; "Enviar mesmo incompleta" é permitido.
- Código da visita: UPA-SIGLA-AAAAMMDD-XXXX. Rascunho por código; a tela inicial lista as visitas em aberto.
- Autosave com versão por relógio e mesclagem de rascunhos (nada se perde entre abas/dispositivos), anexos até 20 por item.

## Limitações conhecidas
- Upload real das fotos e câmera em celular só são validados após a publicação.
- Após alterar módulos (`schema.py`, `sheets_backend.py`) no Streamlit Cloud, faça Reboot do app.
- "Remover" anexo só desvincula; o arquivo permanece no Drive.

## Testes
    pip install pytest && python -m pytest testes
