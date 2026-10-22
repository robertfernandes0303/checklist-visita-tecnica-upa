# -*- coding: utf-8 -*-
"""
evidencias.py - Anexos de evidencia (foto ou documento) do checklist.

O arquivo NUNCA vai para dentro da planilha (limite de 50.000 caracteres por
celula): ele e guardado numa pasta e a planilha recebe so a referencia
(nome + link). Dois destinos:

  1) Google Drive (producao/teste na nuvem): o arquivo e enviado para uma
     subpasta <pasta_evidencias>/<codigo da visita>/. ATENCAO: uma Service
     Account NAO tem cota de armazenamento propria - o envio so funciona se a
     pasta de evidencias estiver num DRIVE COMPARTILHADO (Workspace) em que a
     Service Account seja membro (Gerente de conteudo/Colaborador). Em "Meu
     Drive" de uma pessoa o Google recusa com 403 storageQuotaExceeded.
  2) Pasta local evidencias_locais/ (so para testes sem credenciais; na
     hospedagem em nuvem esse disco e efemero).

Fotos sao reduzidas (lado maior 1600 px, JPEG qualidade 80) antes de guardar.
"""
import io
import json
import os
import re
import uuid

from schema import (
    EXTENSOES_PERMITIDAS,
    LADO_MAX_IMAGEM_PX,
    MAX_MB_IMAGEM_ENTRADA,
    MAX_MB_PDF,
    QUALIDADE_JPEG,
    agora_brasilia,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_EVID_DIR = os.path.join(BASE_DIR, "evidencias_locais")
URL_API = "https://www.googleapis.com/drive/v3/files"
URL_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
MIME_PASTA = "application/vnd.google-apps.folder"
_CACHE_PASTAS = {}


class EvidenciaErro(Exception):
    """Erro com mensagem pronta para mostrar ao auditor."""


def nome_seguro(nome: str) -> str:
    """Nome ASCII seguro, preservando a extensao. 'Relatório Maçã.PDF' -> 'Relatorio_Maca.pdf'."""
    import unicodedata
    nome = os.path.basename((nome or "arquivo").replace("\\", "/"))
    base, ponto, ext = nome.rpartition(".")
    if not ponto:
        base, ext = nome, ""
    sem_acento = lambda t: "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", sem_acento(base)).strip("_") or "arquivo"
    ext = re.sub(r"[^A-Za-z0-9]", "", ext).lower()
    return (base[:70] + ("." + ext if ext else ""))


def preparar_arquivo(dados: bytes, nome_original: str):
    """Valida e normaliza. Retorna (bytes, nome_final, mime, tipo).
    Levanta EvidenciaErro para extensao invalida, arquivo grande ou corrompido."""
    nome = nome_seguro(nome_original)
    ext = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    if ext not in EXTENSOES_PERMITIDAS:
        raise EvidenciaErro("Tipo de arquivo não permitido. Use JPG, PNG ou PDF.")
    base = nome.rsplit(".", 1)[0]

    if ext == "pdf":
        if len(dados) > MAX_MB_PDF * 1024 * 1024:
            raise EvidenciaErro(f"O PDF passa de {MAX_MB_PDF} MB. Envie um arquivo menor.")
        if not dados.startswith(b"%PDF"):
            raise EvidenciaErro("O arquivo não parece ser um PDF válido.")
        return dados, base + ".pdf", "application/pdf", "pdf"

    if len(dados) > MAX_MB_IMAGEM_ENTRADA * 1024 * 1024:
        raise EvidenciaErro(f"A imagem passa de {MAX_MB_IMAGEM_ENTRADA} MB. Envie uma foto menor.")
    try:
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(dados))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img.thumbnail((LADO_MAX_IMAGEM_PX, LADO_MAX_IMAGEM_PX))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=QUALIDADE_JPEG, optimize=True)
    except EvidenciaErro:
        raise
    except Exception as exc:
        raise EvidenciaErro("Não foi possível ler a imagem. Tente outra foto.") from exc
    return buf.getvalue(), base + ".jpg", "image/jpeg", "imagem"


# ---------------------------------------------------------------------------
# Google Drive (via sessao autenticada do gspread - sem dependencia extra)
# ---------------------------------------------------------------------------
def _consulta_escape(texto):
    return texto.replace("\\", "\\\\").replace("'", "\\'")


class UploadAppsScript:
    """Envia o arquivo a um Web App do Google Apps Script (publicado pelo dono da pasta),
    que o grava no Drive dele. Evita OAuth e cota de conta de servico."""

    def __init__(self, url, token):
        self.url, self.token = url, token

    def enviar(self, codigo, nome, dados, mime):
        import base64
        import requests
        payload = {"token": self.token, "pasta": codigo, "nome": nome, "mime": mime,
                   "dados_b64": base64.b64encode(dados).decode("ascii")}
        r = requests.post(self.url, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"},
                          timeout=120, allow_redirects=True)
        try:
            resp = r.json()
        except Exception:
            raise EvidenciaErro("O serviço de upload do Drive não respondeu como esperado. Avise o administrador.")
        if not resp.get("ok"):
            raise EvidenciaErro("Não foi possível guardar o arquivo no Drive: " + str(resp.get("erro", "erro desconhecido"))[:120])
        return resp["link"], resp["id"]


def _listar_apps_script(self, codigo):
    """Arquivos da subpasta `codigo` (lista de dicts) ou levanta EvidenciaErro."""
    import requests
    payload = {"token": self.token, "acao": "listar", "pasta": codigo}
    r = requests.post(self.url, data=json.dumps(payload), headers={"Content-Type": "text/plain;charset=utf-8"},
                      timeout=120, allow_redirects=True)
    try:
        resp = r.json()
    except Exception:
        raise EvidenciaErro("O serviço do Drive não respondeu como esperado. Avise o administrador.")
    if not resp.get("ok"):
        raise EvidenciaErro("Não foi possível consultar a pasta no Drive: " + str(resp.get("erro", "erro desconhecido"))[:120])
    if "arquivos" not in resp:
        raise EvidenciaErro("O serviço do Drive ainda não suporta a consulta da pasta. Avise o administrador.")
    return resp["arquivos"]


UploadAppsScript.listar = _listar_apps_script


def _traduzir_erro_http(resp):
    corpo = ""
    try:
        corpo = resp.text or ""
    except Exception:
        pass
    baixo = corpo.lower()
    if "storagequotaexceeded" in baixo or "storage quota" in baixo:
        return ("Sem espaço no Drive para guardar o arquivo. Se estiver usando conta de serviço, a pasta precisa "
                "estar em um Drive Compartilhado; se estiver usando login de usuário, libere espaço na conta.")
    if resp.status_code == 404:
        return "Pasta de evidências não encontrada ou sem acesso para a conta de serviço."
    if resp.status_code == 403:
        return "Sem permissão para gravar na pasta de evidências do Drive."
    if resp.status_code == 401:
        return "Credencial do Google inválida ou expirada."
    return f"Falha ao enviar o arquivo ao Drive (código {resp.status_code})."


def _pasta_da_visita(sessao, pasta_pai, codigo):
    chave = (pasta_pai, codigo)
    if chave in _CACHE_PASTAS:
        return _CACHE_PASTAS[chave]
    q = (f"name='{_consulta_escape(codigo)}' and '{pasta_pai}' in parents "
         f"and mimeType='{MIME_PASTA}' and trashed=false")
    r = sessao.get(URL_API, params={
        "q": q, "fields": "files(id)", "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true", "pageSize": 1,
    }, timeout=30)
    if r.status_code != 200:
        raise EvidenciaErro(_traduzir_erro_http(r))
    achados = r.json().get("files", [])
    if achados:
        pasta_id = achados[0]["id"]
    else:
        r = sessao.post(URL_API, params={"supportsAllDrives": "true", "fields": "id"},
                        json={"name": codigo, "mimeType": MIME_PASTA, "parents": [pasta_pai]}, timeout=30)
        if r.status_code not in (200, 201):
            raise EvidenciaErro(_traduzir_erro_http(r))
        pasta_id = r.json()["id"]
    _CACHE_PASTAS[chave] = pasta_id
    return pasta_id


def _enviar_drive(sessao, pasta_pai, codigo, nome, dados, mime):
    pasta_id = _pasta_da_visita(sessao, pasta_pai, codigo)
    limite = uuid.uuid4().hex
    meta = json.dumps({"name": nome, "parents": [pasta_id]}).encode("utf-8")
    corpo = (
        f"--{limite}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode("utf-8")
        + meta
        + f"\r\n--{limite}\r\nContent-Type: {mime}\r\n\r\n".encode("utf-8")
        + dados
        + f"\r\n--{limite}--".encode("utf-8")
    )
    r = sessao.post(
        URL_UPLOAD,
        params={"uploadType": "multipart", "supportsAllDrives": "true", "fields": "id,webViewLink"},
        data=corpo, headers={"Content-Type": f"multipart/related; boundary={limite}"}, timeout=120,
    )
    if r.status_code not in (200, 201):
        raise EvidenciaErro(_traduzir_erro_http(r))
    info = r.json()
    return info.get("webViewLink") or f"https://drive.google.com/file/d/{info['id']}/view", info["id"]


def _enviar_local(codigo, nome, dados):
    pasta = os.path.join(LOCAL_EVID_DIR, nome_seguro(codigo))
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    with open(caminho, "wb") as f:
        f.write(dados)
    return caminho, ""


def guardar_evidencia(sessao_drive, pasta_evidencias, codigo, num_item, nome_original, dados):
    """Valida, reduz e guarda o arquivo. `sessao_drive`/`pasta_evidencias`
    None => grava local (modo de teste). Retorna dict para a lista de anexos."""
    conteudo, nome_final, mime, tipo = preparar_arquivo(dados, nome_original)
    nome_unico = f"item{num_item}_{agora_brasilia().strftime('%H%M%S')}_{uuid.uuid4().hex[:4]}_{nome_final}"
    try:
        if isinstance(sessao_drive, UploadAppsScript):
            link, id_arquivo = sessao_drive.enviar(codigo, nome_unico, conteudo, mime)
            destino = "drive"
        elif sessao_drive is not None and pasta_evidencias:
            link, id_arquivo = _enviar_drive(sessao_drive, pasta_evidencias, codigo, nome_unico, conteudo, mime)
            destino = "drive"
        else:
            link, id_arquivo = _enviar_local(codigo, nome_unico, conteudo)
            destino = "local"
    except EvidenciaErro:
        raise
    except Exception as exc:
        if "invalid_grant" in str(exc).lower() or exc.__class__.__name__ == "RefreshError":
            raise EvidenciaErro("A autorização do Google para guardar fotos expirou ou foi revogada. "
                                "Avise o administrador para gerar um novo token (gerar_token_drive.py).") from exc
        raise EvidenciaErro("Falha de conexão ao guardar o arquivo. Tente novamente.") from exc
    return {
        "nome": nome_unico, "tipo": tipo, "tamanho_kb": round(len(conteudo) / 1024, 1),
        "enviado_em": agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
        "link": link, "id_arquivo": id_arquivo, "destino": destino,
    }
