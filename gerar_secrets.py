# -*- coding: utf-8 -*-
"""
gerar_secrets.py

Gera automaticamente o arquivo .streamlit/secrets.toml a partir do arquivo
.json baixado do Google Cloud (a chave da conta de serviço), sem precisar
copiar/colar nada manualmente.

COMO USAR:
  1) Coloque este arquivo (gerar_secrets.py) dentro da pasta "app" do projeto
     (a mesma pasta onde está o app.py).
  2) Abra o Prompt de Comando nessa pasta "app" (com o venv ativado, se tiver).
  3) Rode:
         python gerar_secrets.py "caminho\\para\\o\\arquivo\\baixado.json"

     Exemplo, se o arquivo baixado estiver na pasta Downloads:
         python gerar_secrets.py "C:\\Users\\robert.fernandes\\Downloads\\eventos-adversos-sao-lucas-XXXXX.json"

  4) Pronto — o script cria (ou substitui) o arquivo app\\.streamlit\\secrets.toml
     automaticamente, formatado corretamente.
"""
import json
import os
import sys


def main():
    if len(sys.argv) < 2:
        print("Uso: python gerar_secrets.py \"caminho\\para\\o\\arquivo.json\"")
        sys.exit(1)

    caminho_json = sys.argv[1]

    if not os.path.exists(caminho_json):
        print(f"Arquivo não encontrado: {caminho_json}")
        print("Confira se o caminho está certo (pode arrastar o arquivo .json para dentro")
        print("desta janela do terminal para o Windows preencher o caminho completo sozinho).")
        sys.exit(1)

    with open(caminho_json, encoding="utf-8") as f:
        dados = json.load(f)

    campos_esperados = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "auth_uri", "token_uri",
        "auth_provider_x509_cert_url", "client_x509_cert_url",
    ]
    faltando = [c for c in campos_esperados if c not in dados]
    if faltando:
        print("Aviso: este .json não parece ser o arquivo de chave da conta de serviço.")
        print(f"Campos ausentes: {', '.join(faltando)}")
        print("Confira se você baixou o arquivo certo (Google Cloud > Contas de serviço > Chaves > JSON).")
        sys.exit(1)

    pasta_streamlit = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit")
    os.makedirs(pasta_streamlit, exist_ok=True)
    caminho_saida = os.path.join(pasta_streamlit, "secrets.toml")

    linhas = ["[gcp_service_account]"]
    for campo in campos_esperados:
        valor = dados[campo]
        if campo == "private_key":
            # Triple-quote preserva as quebras de linha reais da chave,
            # exatamente como o Google exige no formato PEM.
            linhas.append(f'{campo} = """{valor}"""')
        else:
            valor_escapado = str(valor).replace("\\", "\\\\").replace('"', '\\"')
            linhas.append(f'{campo} = "{valor_escapado}"')

    conteudo = "\n".join(linhas) + "\n"

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"Pronto! Arquivo criado em: {caminho_saida}")
    print("Agora feche o streamlit (Ctrl+C) e rode 'streamlit run app.py' de novo.")


if __name__ == "__main__":
    main()
