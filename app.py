# -*- coding: utf-8 -*-
"""
app.py - Checklist de Visita Técnica - UPA (Sao Lucas Instituto)
Streamlit + Google Sheets (+ Google Drive para evidencias).
Funciona no navegador e no smartphone.
"""
import html
import os
import threading
import time

import streamlit as st

import schema as sc
import sheets_backend as sb
import evidencias as ev

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(BASE_DIR, "assets", "logo-sao-lucas.png")

st.set_page_config(page_title="Visita Técnica - UPA", page_icon="🩺",
                   layout="centered", initial_sidebar_state="collapsed")

CSS = """
<style>
:root {color-scheme: only light;}
html, body, .stApp {color-scheme: only light;}
:root {--azul:#003366; --vibrante:#00AEEF; --agua:#008B8B; --amarelo:#F2C94C; --laranja:#F2994A;
       --cinza:#828282; --texto:#2F3B42; --raio:16px;
       --vidro: rgba(255,255,255,.58); --vidro-borda: rgba(255,255,255,.85);
       --sombra: 0 6px 18px rgba(0,51,102,.10), 0 1px 3px rgba(0,51,102,.08);
       --brilho: inset 0 1px 0 rgba(255,255,255,.95), inset 0 -1px 0 rgba(0,51,102,.04);}
html, body, .stApp {background-color: #EEF5F9 !important; background-image: none !important;}
header[data-testid="stHeader"] {display: none;}
/* Botões de anexo em português e mais claros no celular */
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p {font-size: 0 !important;}
[data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] p::after {
  content: "Escolher arquivo"; font-size: 1rem;}
[data-testid="stFileUploader"]:has(input[capture]) button [data-testid="stMarkdownContainer"] p::after {
  content: "Abrir câmera";}
[data-testid="stFileUploaderDropzoneInstructions"] {display: none !important;}
[data-testid="stFileUploaderDropzone"] {padding: 0.5rem !important;}
.block-container {padding-top: 1.6rem !important; padding-bottom: 4rem; max-width: 760px;}
h1,h2,h3,h4 {color: var(--azul) !important;}
.sl-titulo {font-size: 1.4rem; font-weight: 700; color: var(--azul); margin: .2rem 0 .1rem 0;}
.sl-sub {color: var(--cinza); font-size: .92rem; margin-bottom: .6rem;}

/* efeito vidro: superficie translucida, borda clara, sombra suave e brilho interno */
.sl-previsto, .sl-aviso, details, div[data-testid="stVerticalBlockBorderWrapper"],
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div,
div[data-testid="stFileUploaderDropzone"], div[data-testid="stCameraInput"] > div {
  border-radius: var(--raio) !important; border: 1px solid var(--vidro-borda) !important;
  box-shadow: var(--sombra), var(--brilho) !important;
  -webkit-backdrop-filter: blur(10px) saturate(130%); backdrop-filter: blur(10px) saturate(130%);}
div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div,
div[data-testid="stFileUploaderDropzone"] {background: var(--vidro) !important;}
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {background: transparent !important;}
details, div[data-testid="stVerticalBlockBorderWrapper"] {background: rgba(255,255,255,.52) !important;}
.sl-previsto {background: rgba(214,238,250,.70); border-left: 4px solid var(--vibrante) !important; color: var(--texto);}
.sl-previsto b {color: var(--azul); font-size:.72rem; letter-spacing:.04em;}
.sl-aviso {background: rgba(252,243,210,.78); border-left: 4px solid var(--amarelo) !important; color: var(--texto);
  padding:.55rem .8rem; font-size:.85rem; margin:.3rem 0;}
.sl-previsto {padding:.6rem .8rem; font-size:.88rem; margin:.3rem 0 .6rem 0;}
.sl-badge {font-size:.8rem; color: var(--agua); margin:.1rem 0 .4rem 0; font-weight:600;}
.sl-codigo {font-family: monospace; background: rgba(214,238,250,.8); padding:.1rem .4rem; border-radius:8px; color: var(--azul);}

/* botoes: relevo de vidro */
div[data-testid="stButton"] button {min-height: 2.8rem; border-radius: 14px !important; transition: all .15s ease;
  border: 1px solid var(--vidro-borda) !important; background: rgba(255,255,255,.7); color: var(--texto);
  box-shadow: var(--sombra), var(--brilho); backdrop-filter: blur(8px);}
div[data-testid="stButton"] button:hover {transform: translateY(-1px); box-shadow: 0 10px 22px rgba(0,51,102,.16), var(--brilho);
  border-color: var(--vibrante) !important; color: var(--azul);}
div[data-testid="stButton"] button[kind="primary"] {background: linear-gradient(180deg, #0B4A85 0%, var(--azul) 100%);
  border: 1px solid rgba(255,255,255,.35) !important; color:#fff;
  box-shadow: 0 8px 18px rgba(0,51,102,.28), inset 0 1px 0 rgba(255,255,255,.35);}
div[data-testid="stButton"] button[kind="primary"]:hover {background: linear-gradient(180deg, #19BDFB 0%, var(--vibrante) 100%); color:#fff;}
div[data-testid="stButton"] button:disabled {opacity:.55; transform:none; box-shadow: none;}
div[data-testid="stButton"] button[kind="primary"]:disabled {background:#C9D6DF; border-color:#C9D6DF !important; color:#fff;}

div[data-testid="stProgressBarTrack"] {background-color: #D9E6EE !important; border-radius: 999px; box-shadow: inset 0 1px 3px rgba(0,51,102,.15);}
div[data-testid="stProgressBarTrack"] > div {background-color: var(--laranja) !important; border-radius: 999px;}
details summary {border-radius: var(--raio);}
div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] p {color: #6B6B6B !important;}
h3 {font-size: 1.25rem !important;}
img {border-radius: 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

ICONE_FONTE = {sc.OBSERVADO: "👁️", sc.INFORMADO: "🗣️", sc.OBS_INF: "👁️🗣️", sc.NAO_VERIF: "❔", sc.NAO_SE_APLICA: "➖"}


def _respondido(r):
    """Item respondido: tem valor/resposta, ou foi marcado Não verificado / Não se aplica."""
    r = r or {}
    return bool(str(r.get("resposta", "")).strip()) or r.get("fonte") in (sc.NAO_VERIF, sc.NAO_SE_APLICA)


def _verificado(r):
    r = r or {}
    return bool(str(r.get("resposta", "")).strip()) and r.get("fonte") in sc.FONTES_VERIFICADAS


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
def _estado_inicial():
    return {
        "avisou_mescla": False,
        "etapa": "cabecalho", "codigo": None, "hospital": "", "cidade": "", "uf": "", "edital": "",
        "responsavel": "", "acompanhante": "", "horario": "", "solo_essenciais": False, "data_visita": sc.agora_brasilia().date(),
        "inicio": None, "respostas": {}, "anexos": {},
        "visitados": [], "concluidos": [], "grupo_atual": 0, "versao": 0, "anexos_removidos": [],
        "impactos": {}, "contador_lin": 0, "gen_w": 0,
        "camera_item": None, "contador_up": {}, "contador_cam": {}, "rascunhos_achados": None,
        "resultado_envio": None,
    }


def _garantir_estado():
    for k, v in _estado_inicial().items():
        if k not in st.session_state:
            st.session_state[k] = v


_garantir_estado()
S = st.session_state


def _resetar():
    for k in list(S.keys()):
        del S[k]
    _garantir_estado()


def _dados_rascunho():
    return {
        "codigo_visita": S.codigo, "hospital": S.hospital, "cidade": S.cidade, "uf": S.uf, "edital": S.edital,
        "responsavel_visita": S.responsavel, "acompanhante": S.acompanhante, "horario": S.horario,
        "data_visita": S.data_visita.isoformat(), "timestamp_inicio": S.inicio,
        "respostas": {str(k): v for k, v in S.respostas.items()},
        "anexos": {str(k): v for k, v in S.anexos.items()},
        "grupos_visitados": S.visitados, "grupos_concluidos": S.concluidos,
        "anexos_removidos": S.anexos_removidos,
        "impactos": {str(k): v for k, v in S.impactos.items()},
    }


def _autosave():
    if not S.codigo:
        return
    S.versao = max(S.versao + 1, time.time_ns() // 1000)   # relogio: vale entre sessoes diferentes
    dados = _dados_rascunho()
    t = threading.Thread(target=sb.salvar_rascunho,
                         args=(S.codigo, S.hospital, S.responsavel, dados, S.versao), daemon=True)
    t.start()



def _k(pref, n):
    """Chave de widget com geracao: ao absorver dados de outra sessao a geracao sobe e os campos nascem de novo."""
    return f"{pref}{n}_g{S.gen_w}"


def _absorver_mesclado():
    """Se outra sessao gravou a mesma visita, incorpora o que veio de la (nada se perde)."""
    if not S.codigo or S.etapa in ("cabecalho", "bloqueio", "retomar_lista", "confirmacao"):
        return
    m = sb.mesclado_pendente(S.codigo)
    if not m:
        return
    novos = {int(k): v for k, v in (m.get("respostas") or {}).items()}
    novos_anexos = {int(k): v for k, v in (m.get("anexos") or {}).items()}
    if novos == S.respostas and novos_anexos == S.anexos:
        return                                    # nada novo de fora (so reordenacao)
    S.gen_w += 1                                  # novas chaves de widget: campos refletem os dados mesclados
    S.respostas = novos
    S.impactos = {int(k): v for k, v in (m.get("impactos") or {}).items()}
    S.anexos = novos_anexos
    S.anexos_removidos = list(m.get("anexos_removidos") or [])
    S.visitados = list(m.get("grupos_visitados") or S.visitados)
    S.concluidos = list(m.get("grupos_concluidos") or S.concluidos)
    S.avisou_mescla = True
    st.rerun()


def _carregar_dados(entrada):
    d = entrada["dados"]
    from datetime import date
    S.codigo = d["codigo_visita"]
    S.hospital = d.get("hospital", "")
    S.cidade, S.uf = d.get("cidade", ""), d.get("uf", "")
    if not S.cidade and d.get("cidade_uf"):  # rascunhos antigos
        partes = d["cidade_uf"].replace("-", "/").split("/")
        S.cidade = partes[0].strip()
        S.uf = partes[1].strip().upper() if len(partes) > 1 and partes[1].strip().upper() in sc.UFS else ""
    S.edital = d.get("edital", "")
    S.responsavel = d.get("responsavel_visita", "")
    S.acompanhante = d.get("acompanhante", "")
    S.horario = d.get("horario", "")
    try:
        S.data_visita = date.fromisoformat(d.get("data_visita"))
    except Exception:
        S.data_visita = sc.agora_brasilia().date()
    S.inicio = d.get("timestamp_inicio") or sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S")
    S.respostas = {int(k): v for k, v in d.get("respostas", {}).items()}
    S.impactos = {int(k): v for k, v in (d.get("impactos") or {}).items()}
    S.anexos = {int(k): v for k, v in d.get("anexos", {}).items()}
    S.visitados = d.get("grupos_visitados", [])
    S.concluidos = d.get("grupos_concluidos", [])
    S.contador_lin += 1
    S.versao = 0
    S.anexos_removidos = list(d.get("anexos_removidos", []))
    S.etapa = "menu"


def _iniciar_nova():
    S.codigo = sc.gerar_codigo_visita(S.hospital)
    S.inicio = sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S")
    S.respostas, S.impactos, S.anexos = {}, {}, {}
    S.visitados, S.concluidos = [], []
    S.etapa = "menu"
    _autosave()


# ---------------------------------------------------------------------------
# Cabecalho
# ---------------------------------------------------------------------------
VERSAO_APP = "1.0 UPA"
ANEXOS_ESPERADOS = 20


def _topo():
    if os.path.exists(LOGO):
        st.image(LOGO, width=158)
    st.markdown('<div class="sl-titulo">Checklist de Visita Técnica</div>', unsafe_allow_html=True)
    st.caption(f"v{VERSAO_APP} · até {sc.MAX_ANEXOS_POR_ITEM} anexos por item")
    if S.get("avisou_mescla"):
        st.info("Outra pessoa ou aba também salvou esta visita. Os dados foram reunidos e nada foi perdido.")
    if not sb.modo_google():
        st.warning("Modo de teste: as respostas NÃO estão sendo gravadas na planilha do Google (credenciais não configuradas).")
    if sc.MAX_ANEXOS_POR_ITEM != ANEXOS_ESPERADOS:
        st.warning("Parte do código do app está desatualizada (versão antiga em memória). "
                   "Avise o responsável para reiniciar o app (Manage app > Reboot).")


def _rodape_codigo():
    if S.codigo:
        st.caption(f"Código da visita: **{S.codigo}** — guarde para retomar depois.")
        est = sb.estado_autosave(S.codigo)
        if est and not est["ok"]:
            st.error("⚠️ O salvamento automático falhou. Seus dados NÃO estão protegidos. "
                     f"Não feche a página; tente novamente. ({est['msg']})")


def tela_bloqueio():
    _topo()
    st.error("Não foi possível verificar se já existe uma visita em andamento (falha de conexão com a base). "
             "Para evitar duplicidade ou perda de dados, nada foi iniciado.")
    if st.button("Tentar novamente", type="primary"):
        S.etapa = "cabecalho"
        st.rerun()


def _resumo_rascunho(r):
    d = r.get("dados") or {}
    feitos = sum(1 for v in (d.get("respostas") or {}).values() if _respondido(v))
    return feitos


def _visitas_em_aberto():
    """Mostra as visitas em andamento para o auditor escolher e continuar (sem digitar codigo)."""
    abertas = sb.listar_rascunhos_abertos()
    if abertas == sb.ERRO_VERIFICACAO_RASCUNHO:
        st.warning("Não foi possível consultar as visitas em aberto agora. Verifique a conexão e tente de novo "
                   "antes de iniciar uma nova visita, para evitar duplicidade.")
        if st.button("Tentar novamente", key="tentar_abertas"):
            st.rerun()
        S.abertas_ok = False
        return
    S.abertas_ok = True
    if not abertas:
        return
    st.markdown(f"### Visitas em aberto ({len(abertas)})")
    st.caption("Toque em Continuar para retomar de onde parou.")
    for r in abertas:
        with st.container(border=True):
            if r["corrompido"]:
                st.markdown(f"**{r['codigo']}** — rascunho ilegível")
                continue
            feitos = _resumo_rascunho(r)
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{html.escape(r['hospital'] or '—')}**  \n"
                        f"{html.escape(r['responsavel'] or '—')} · atualizado em {r['atualizado_em'] or '—'}  \n"
                        f"{feitos} de {sc.TOTAL_ITENS} itens · `{r['codigo']}`")
            if c2.button("Continuar", key=f"abrir_rasc_{r['codigo']}", type="primary", use_container_width=True):
                _carregar_dados(r)
                st.rerun()
    st.divider()


def tela_cabecalho():
    _topo()
    _visitas_em_aberto()
    st.markdown("### Nova visita")
    st.markdown('<div class="sl-sub">Preencha os dados da visita para começar.</div>', unsafe_allow_html=True)
    S.hospital = st.text_input("Nome da unidade *", value=S.hospital, placeholder="Digite o nome da unidade")
    c1, c2 = st.columns([3, 1])
    S.cidade = c1.text_input("Cidade", value=S.cidade)
    S.uf = c2.selectbox("UF", sc.UFS, index=sc.UFS.index(S.uf) if S.uf in sc.UFS else None, placeholder="UF") or ""
    S.data_visita = st.date_input("Data da visita *", value=S.data_visita, max_value=sc.agora_brasilia().date(),
                                  format="DD/MM/YYYY")
    S.responsavel = st.text_input("Responsável pela visita *", value=S.responsavel)
    S.acompanhante = st.text_input("Nome de quem acompanhou (unidade)", value=S.acompanhante)
    S.edital = st.text_input("Edital / Processo (se houver)", value=S.edital)

    if st.button("Iniciar visita", type="primary", use_container_width=True):
        if not S.get("abertas_ok", True):
            st.warning("Aguarde a consulta das visitas em aberto antes de iniciar uma nova visita.")
        elif not (S.hospital.strip() and S.responsavel.strip()):
            st.warning("Informe o nome da unidade e o responsável pela visita.")
        else:
            S.hospital, S.responsavel = S.hospital.strip(), S.responsavel.strip()
            achados = sb.listar_rascunhos_hospital(S.hospital)
            if achados == sb.ERRO_VERIFICACAO_RASCUNHO:
                S.etapa = "bloqueio"
            elif achados:
                S.rascunhos_achados = achados
                S.etapa = "retomar_lista"
            else:
                _iniciar_nova()
            st.rerun()


def tela_retomar_lista():
    _topo()
    st.info(f"Há visita(s) em andamento para **{S.hospital}**. Deseja continuar uma delas?")
    for r in S.rascunhos_achados:
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"`{r['codigo']}` — {r['responsavel'] or '—'} — atualizado em {r['atualizado_em'] or '—'}")
        if r["corrompido"]:
            c2.caption("ilegível")
        elif c2.button("Continuar", key=f"cont_{r['codigo']}"):
            _carregar_dados(r)
            st.rerun()
    st.divider()
    cA, cB = st.columns(2)
    if cA.button("Começar uma nova visita", type="primary", use_container_width=True):
        _iniciar_nova()
        st.rerun()
    if cB.button("Voltar", use_container_width=True):
        S.etapa = "cabecalho"
        st.rerun()


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
def _respondidos():
    return sum(1 for g in sc.GRUPOS for i in g["itens"] if _respondido(S.respostas.get(i["num"])))


def _status_grupo(gi):
    if gi in S.concluidos:
        return "✅ Concluído"
    itens = sc.GRUPOS[gi]["itens"]
    if any(_respondido(S.respostas.get(i["num"])) for i in itens) or gi in S.visitados:
        return "🟡 Em andamento"
    return "⚪ Não iniciado"


def tela_menu():
    _topo()
    st.markdown(f"**{html.escape(S.hospital)}** · {S.data_visita.strftime('%d/%m/%Y')}")
    resp = _respondidos()
    ess = sum(1 for g in sc.GRUPOS for i in g["itens"] if i["foco"] == sc.ESSENCIAL and _respondido(S.respostas.get(i["num"])))
    st.progress(resp / sc.TOTAL_ITENS, text=f"{resp} de {sc.TOTAL_ITENS} itens respondidos")
    st.caption(f"Essenciais: {ess}/{sc.TOTAL_ESSENCIAIS} · Complementares: {resp - ess}/{sc.TOTAL_COMPLEMENTARES}")
    _rodape_codigo()
    st.markdown('<div class="sl-aviso">📵 Não fotografe pacientes, rostos ou prontuários com dados '
                'identificáveis. Fotografe apenas estrutura, equipamentos e documentos do serviço.</div>',
                unsafe_allow_html=True)
    S.solo_essenciais = st.toggle("Mostrar só os itens essenciais (visita rápida)", value=S.solo_essenciais)
    for gi, g in enumerate(sc.GRUPOS):
        itens = g["itens"]
        if S.solo_essenciais and not any(i["foco"] == sc.ESSENCIAL for i in itens):
            continue
        feitos = sum(1 for i in itens if _respondido(S.respostas.get(i["num"])))
        ne = sum(1 for i in itens if i["foco"] == sc.ESSENCIAL)
        foco = f"{ne} essenciais" if ne else "complementar"
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{g['nome']}**  \n{_status_grupo(gi)} · {feitos}/{len(itens)} · {foco}")
        if c2.button("Abrir", key=f"abrir_{gi}", use_container_width=True):
            S.grupo_atual = gi
            if gi not in S.visitados:
                S.visitados.append(gi)
            S.camera_item = None
            S.etapa = "grupo"
            _autosave()
            st.rerun()
    st.divider()
    with st.expander("Alguma foto anexada não aparece? Recuperar anexos"):
        st.caption("Busca na pasta desta visita no Drive as fotos e PDFs enviados que não foram ligados aos itens "
                   "e os religa ao item certo. Anexos que você removeu não voltam.")
        if st.button("Recuperar anexos do Drive", key="recuperar_anexos", use_container_width=True):
            with st.spinner("Consultando o Drive..."):
                r = sb.recuperar_anexos_do_drive(S.codigo)
            if r["erro"]:
                st.error(r["erro"])
            else:
                dados = {"anexos": S.anexos, "anexos_removidos": S.anexos_removidos}
                for num, info in r["pares"]:
                    sb._juntar_anexo(dados, num, info)
                S.anexos = {int(k): v for k, v in dados["anexos"].items()}
                _autosave()
                st.success(f"{r['na_pasta']} arquivo(s) na pasta do Drive; {r['novos']} religado(s) aos itens.")
    visiveis = [gi for gi, g in enumerate(sc.GRUPOS)
                if not S.solo_essenciais or any(i["foco"] == sc.ESSENCIAL for i in g["itens"])]
    todos = all(gi in S.concluidos for gi in visiveis)
    if st.button("Enviar visita completa", type="primary", disabled=not todos, use_container_width=True):
        S.etapa = "confirmar_envio"
        st.rerun()
    if not todos:
        if st.button("Enviar mesmo incompleta", use_container_width=True):
            S.etapa = "confirmar_envio"
            st.rerun()
        st.caption(f"O envio completo é liberado quando as {len(visiveis)} seções listadas estiverem concluídas.")


# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------
def _cb_resposta(num):
    r = S.respostas.setdefault(num, {})
    r["resposta"] = st.session_state.get(_k("resposta_", num), "")
    agora = sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S")
    r["atualizado_em"] = agora
    r.setdefault("respondido_em", agora)
    _autosave()


def _cb_fonte(num):
    r = S.respostas.setdefault(num, {})
    r["fonte"] = st.session_state.get(_k("fonte_", num))
    agora = sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S")
    r["atualizado_em"] = agora
    r.setdefault("respondido_em", agora)
    _autosave()


def _cb_obs(num):
    r = S.respostas.setdefault(num, {})
    r["obs"] = st.session_state.get(_k("obs_", num), "")
    r["atualizado_em"] = sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S")
    _autosave()


def _cb_impacto(gi):
    S.impactos[gi] = st.session_state.get(_k("impsec_", gi), "")
    _autosave()


def _adicionar_anexos(num, arquivos):
    """Envia os arquivos [(nome, bytes), ...] ao Drive e os registra no rascunho numa thread que NAO
    e interrompida se a pessoa sair do app no meio (celular bloqueado, troca de app): nenhum anexo
    fica orfao no Drive. Devolve True se ao menos um foi guardado."""
    sessao, pasta = sb.drive_para_evidencias()
    codigo = S.codigo
    saida = {"infos": [], "erros": []}

    def tarefa():
        for nome, dados in arquivos:
            try:
                info = ev.guardar_evidencia(sessao, pasta, codigo, num, nome, dados)
                sb.registrar_anexo_rascunho(codigo, num, info)
                saida["infos"].append(info)
            except ev.EvidenciaErro as exc:
                saida["erros"].append(f"{nome}: {exc}")
            except Exception as exc:
                saida["erros"].append(f"{nome}: falha ao guardar ({exc.__class__.__name__}). Tente novamente.")

    t = threading.Thread(target=tarefa, daemon=True)
    t.start()
    t.join()
    for erro in saida["erros"]:
        st.error(erro)
    lista = S.anexos.setdefault(num, [])
    for info in saida["infos"]:
        chave = sb._chave_anexo(info)
        if not any(sb._chave_anexo(x) == chave for x in lista):
            lista.append(info)
    return bool(saida["infos"])


def _adicionar_anexo(num, nome, dados):
    return _adicionar_anexos(num, [(nome, dados)])


def _bloco_observacao(item):
    num = item["num"]
    anexos = S.anexos.get(num, [])
    r = S.respostas.get(num, {})
    partes = []
    if str(r.get("obs", "")).strip():
        partes.append("observação")
    if anexos:
        partes.append(f"{len(anexos)} anexo(s)")
    # O badge e SEMPRE renderizado (vazio quando nao ha conteudo): se ele aparecesse/sumisse,
    # a posicao do expander mudaria e o Streamlit o fecharia a cada atualizacao.
    texto_badge = f'<div class="sl-badge">● {" · ".join(partes)}</div>' if partes else '<div class="sl-badge">&nbsp;</div>'
    st.markdown(texto_badge, unsafe_allow_html=True)

    with st.expander("📝 Observação e evidências"):
        st.text_area("Observação", value=r.get("obs", ""), key=_k("obs_", num), height=90,
                     on_change=_cb_obs, args=(num,), placeholder="Detalhes, quem informou, documento visto…")

        restantes = sc.MAX_ANEXOS_POR_ITEM - len(anexos)
        if restantes <= 0:
            st.info(f"Limite de {sc.MAX_ANEXOS_POR_ITEM} anexos por item atingido.")
        else:
            foto = st.file_uploader(
                "📷 Tirar foto", type=["jpg", "jpeg", "png"], accept_multiple_files=False,
                key=f"cam_{num}_{S.contador_cam.get(num, 0)}",
                help="Abre a câmera traseira do celular em tela cheia.")
            if foto is not None:
                with st.spinner("Guardando a foto…"):
                    ok = _adicionar_anexo(num, f"foto_{sc.agora_brasilia().strftime('%H%M%S')}.jpg",
                                          foto.getvalue())
                S.contador_cam[num] = S.contador_cam.get(num, 0) + 1
                if ok:
                    _autosave()
                    st.rerun()

            arqs = st.file_uploader(
                "📎 Anexar arquivo (foto ou PDF)", type=sc.EXTENSOES_PERMITIDAS, accept_multiple_files=True,
                key=f"up_{num}_{S.contador_up.get(num, 0)}",
                help=f"JPG, PNG ou PDF. Até {sc.MAX_MB_PDF} MB por PDF; máx. {sc.MAX_ANEXOS_POR_ITEM} por item.")
            if arqs:
                vagas = sc.MAX_ANEXOS_POR_ITEM - len(S.anexos.get(num, []))
                if len(arqs) > vagas:
                    st.warning("Limite de anexos atingido; arquivos excedentes foram ignorados.")
                with st.spinner("Guardando arquivo(s)…"):
                    gravou = _adicionar_anexos(num, [(x.name, x.getvalue()) for x in arqs[:max(vagas, 0)]])
                S.contador_up[num] = S.contador_up.get(num, 0) + 1
                if gravou:
                    _autosave()
                    st.rerun()

        for idx, a in enumerate(list(S.anexos.get(num, []))):
            c1, c2 = st.columns([4, 1])
            link = a.get("link", "")
            if link.startswith("http"):
                c1.markdown(f"[{a['nome']}]({link}) · {a['tamanho_kb']} KB")
            else:
                c1.markdown(f"{a['nome']} · {a['tamanho_kb']} KB (local)")
            if c2.button("remover", key=f"rm_{num}_{idx}"):
                removido = S.anexos[num].pop(idx)
                S.anexos_removidos.append(removido.get("id_arquivo") or removido.get("link") or removido.get("nome"))
                _autosave()
                st.rerun()


def _card_item(item):
    num = item["num"]
    r = S.respostas.get(num, {})
    foco = "🔴 Essencial" if item["foco"] == sc.ESSENCIAL else "⚪ Complementar"
    st.markdown(f"**{item['ref']}** {html.escape(item['texto'])}")
    st.caption(foco + (f" · unidade: {item['unidade']}" if item.get("unidade") else ""))
    st.text_input("Resposta / valor", value=r.get("resposta", ""), key=_k("resposta_", num),
                  on_change=_cb_resposta, args=(num,),
                  placeholder=(f"Informe o valor ({item['unidade']})" if item.get("unidade") else "Informe a resposta"))
    atual = r.get("fonte")
    st.radio("Fonte", sc.OPCOES_FONTE, index=sc.OPCOES_FONTE.index(atual) if atual in sc.OPCOES_FONTE else None,
             horizontal=True, key=_k("fonte_", num), on_change=_cb_fonte, args=(num,),
             format_func=lambda o: f"{ICONE_FONTE[o]} {o}")
    if _verificado(r):
        st.caption("✅ Verificado")
    _bloco_observacao(item)
    st.divider()


def tela_grupo():
    gi = S.grupo_atual
    g = sc.GRUPOS[gi]
    _topo()
    st.markdown(f"### {g['nome']}")
    st.caption(f"{S.hospital} · {S.codigo}")
    itens = [i for i in g["itens"] if i["foco"] == sc.ESSENCIAL] if S.solo_essenciais else g["itens"]
    if S.solo_essenciais and not itens:
        itens = g["itens"]
    for item in itens:
        _card_item(item)
    st.text_area("Impacto na proposta e providências São Lucas (desta seção)", value=S.impactos.get(gi, ""),
                 key=_k("impsec_", gi), height=110, on_change=_cb_impacto, args=(gi,),
                 placeholder="Como o que foi visto afeta a proposta; providências a tomar…")
    _camera_traseira()
    faltam = [i["ref"] for i in itens if not _respondido(S.respostas.get(i["num"]))]
    _rodape_codigo()
    c1, c2 = st.columns(2)
    if c1.button("Salvar e voltar ao menu", use_container_width=True):
        S.camera_item = None
        _autosave()
        S.etapa = "menu"
        st.rerun()
    if c2.button("Concluir seção", type="primary", use_container_width=True):
        if faltam:
            st.warning("Responda todos os itens (ou marque Não verificado / Não se aplica) antes de concluir. Faltam: " + ", ".join(faltam))
        else:
            if gi not in S.concluidos:
                S.concluidos.append(gi)
            S.camera_item = None
            _autosave()
            S.etapa = "menu"
            st.rerun()


# ---------------------------------------------------------------------------
# Envio
# ---------------------------------------------------------------------------

def _camera_traseira():
    """Faz o botão 'Tirar foto' abrir a câmera nativa (traseira, tela cheia) no celular."""
    codigo = """
<script>
(function(){
  var d = window.parent.document;
  function ajustar(){
    d.querySelectorAll('[data-testid="stFileUploader"]').forEach(function(w){
      if ((w.innerText || '').indexOf('Tirar foto') === -1) return;
      var inp = w.querySelector('input[type=file]');
      if (inp && inp.getAttribute('capture') !== 'environment'){
        inp.setAttribute('capture','environment');
        inp.setAttribute('accept','image/*');
      }
    });
  }
  ajustar();
  if (!window.parent.__capObs){
    window.parent.__capObs = new MutationObserver(ajustar);
    window.parent.__capObs.observe(d.body,{childList:true,subtree:true});
  }
})();
</script>"""
    if hasattr(st, "iframe"):
        st.iframe(codigo, height=1)
    else:
        import streamlit.components.v1 as components
        components.html(codigo, height=0)

def _montar_envio():
    data_txt = S.data_visita.strftime("%d/%m/%Y")
    itens, evidencias, secoes = [], [], []
    verif = nverif = nasp = nao_pre = total_anexos = 0
    resp_ess = resp_comp = 0
    for gi, g in enumerate(sc.GRUPOS):
        for it in g["itens"]:
            n = it["num"]
            r = S.respostas.get(n, {})
            feito = _respondido(r)
            if feito:
                if it["foco"] == sc.ESSENCIAL:
                    resp_ess += 1
                else:
                    resp_comp += 1
            else:
                nao_pre += 1
            if r.get("fonte") == sc.NAO_VERIF:
                nverif += 1
            elif r.get("fonte") == sc.NAO_SE_APLICA:
                nasp += 1
            elif _verificado(r):
                verif += 1
            anx = S.anexos.get(n, [])
            total_anexos += len(anx)
            itens.append({
                "Código da Visita": S.codigo, "Unidade": S.hospital, "Data da Visita": data_txt,
                "Seção": g["nome"], "ID": it["ref"], "Foco": sc.ROTULO_FOCO[it["foco"]],
                "Pergunta ou dado a levantar": it["texto"], "Resposta / valor": r.get("resposta", ""),
                "Fonte": r.get("fonte") or "", "Verificado (OK)": "Sim" if _verificado(r) else "Não",
                "Observação": r.get("obs", ""), "Qtde de Anexos": len(anx),
                "Respondido em": r.get("respondido_em", "") if feito else "",
            })
            for a in anx:
                evidencias.append({
                    "Código da Visita": S.codigo, "Unidade": S.hospital, "ID": it["ref"], "Ref.": it["ref"],
                    "Arquivo": a["nome"], "Tipo": a["tipo"], "Tamanho (KB)": a["tamanho_kb"],
                    "Enviado em": a["enviado_em"], "Link / Caminho": a["link"],
                })
        txt = str(S.impactos.get(gi, "")).strip()
        if txt:
            secoes.append({"Código da Visita": S.codigo, "Unidade": S.hospital, "Nº da Seção": gi + 1,
                           "Seção": g["nome"], "Impacto na proposta e providências São Lucas": txt})
    visita = {
        "Código da Visita": S.codigo, "Unidade": S.hospital, "Cidade": S.cidade, "UF": S.uf,
        "Edital / Processo": S.edital, "Data da Visita": data_txt, "Horário": S.horario or str(S.inicio or "")[11:16],
        "Visitantes": S.responsavel, "Acompanhante / função": S.acompanhante,
        "Início do Preenchimento": S.inicio,
        "Fim do Preenchimento (Envio)": sc.agora_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
        "Status da Visita": "Completa" if nao_pre == 0 else "Incompleta",
        "Total de Itens": sc.TOTAL_ITENS, "Itens Respondidos": sc.TOTAL_ITENS - nao_pre,
        "Essenciais Respondidos": resp_ess, "Complementares Respondidos": resp_comp,
        "Total Verificados": verif, "Total Não Verificados": nverif, "Total Não se Aplica": nasp,
        "Total Não Preenchido": nao_pre, "Total de Anexos": total_anexos,
        "Seções com Impacto Registrado": len(secoes),
    }
    return visita, itens, evidencias, secoes


def tela_confirmar():
    _topo()
    visita, itens, evidencias, secoes = _montar_envio()
    st.markdown("### Confirmar envio")
    st.markdown(f"**{html.escape(S.hospital)}** · {visita['Data da Visita']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verificados", visita["Total Verificados"])
    c2.metric("Não verif.", visita["Total Não Verificados"])
    c3.metric("N/A", visita["Total Não se Aplica"])
    c4.metric("Em branco", visita["Total Não Preenchido"])
    st.write(f"Essenciais: **{visita['Essenciais Respondidos']}/{sc.TOTAL_ESSENCIAIS}** · "
             f"Anexos: **{visita['Total de Anexos']}** · Seções com impacto: **{visita['Seções com Impacto Registrado']}**")
    if visita["Total Não Preenchido"]:
        st.warning(f"{visita['Total Não Preenchido']} item(ns) sem resposta. A visita será registrada como "
                   "**Incompleta**.")
    cA, cB = st.columns(2)
    if cA.button("Confirmar e enviar", type="primary", use_container_width=True):
        with st.spinner("Gravando…"):
            ok, modo, msg = sb.salvar_auditoria(visita, itens, evidencias, secoes)
        if ok:
            sb.apagar_rascunho(S.codigo)
            S.resultado_envio = {"modo": modo, "msg": msg, "codigo": S.codigo, "status": visita["Status da Visita"]}
            S.etapa = "confirmacao"
        else:
            st.error(msg + " Seus dados continuam salvos; tente novamente.")
            return
        st.rerun()
    if cB.button("Voltar", use_container_width=True):
        S.etapa = "menu"
        st.rerun()


def tela_confirmacao():
    _topo()
    r = S.resultado_envio
    st.success(f"Visita enviada — status: **{r['status']}**.")
    st.markdown(f"Código: <span class='sl-codigo'>{r['codigo']}</span>", unsafe_allow_html=True)
    if r["modo"] == "local_fallback":
        st.warning(r["msg"])
    else:
        st.caption(r["msg"])
    if st.button("Registrar nova visita", type="primary"):
        _resetar()
        st.rerun()


ETAPAS = {
    "bloqueio": tela_bloqueio, "cabecalho": tela_cabecalho, "retomar_lista": tela_retomar_lista,
    "menu": tela_menu, "grupo": tela_grupo, "confirmar_envio": tela_confirmar, "confirmacao": tela_confirmacao,
}
_absorver_mesclado()
ETAPAS.get(S.etapa, tela_cabecalho)()
