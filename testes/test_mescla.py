"""Duas sessoes na mesma visita: ninguem apaga o trabalho do outro; versao vale entre sessoes."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sheets_backend as sb
from test_cota import AbaFalsa, _preparar


def _d(resp=None, anexos=None, visitados=None, removidos=None):
    return {"codigo_visita": "C1", "respostas": resp or {}, "previsto_informado": {},
            "anexos": anexos or {}, "grupos_visitados": visitados or [], "grupos_concluidos": [],
            "anexos_removidos": removidos or []}


def _r(sit, ts, **kw):
    return {"situacao": sit, "respondido_em": ts, "atualizado_em": ts, **kw}


def _lido(aba, i=1):
    return json.loads("".join(aba.linhas[i][5:]))


def test_mescla_nao_perde_itens_de_nenhum_lado():
    a = _d({"1": _r("OK", "19/10/2026 09:00:00"), "2": _r("OK", "19/10/2026 09:01:00")})
    b = _d({"3": _r("Parcial", "19/10/2026 09:05:00")}, visitados=[2])
    m = sb.mesclar_dados(a, b)
    assert set(m["respostas"]) == {"1", "2", "3"}


def test_mescla_item_em_conflito_vale_o_mais_recente_e_junta_campos():
    velho = _d({"1": _r("OK", "19/10/2026 09:00:00", achado="texto antigo", impacto="impacto A")})
    novo = _d({"1": _r("Parcial", "19/10/2026 09:30:00", achado="texto novo", impacto="")})
    m = sb.mesclar_dados(velho, novo)["respostas"]["1"]
    assert m["situacao"] == "Parcial" and m["achado"] == "texto novo" and m["impacto"] == "impacto A"
    m2 = sb.mesclar_dados(novo, velho)["respostas"]["1"]      # sessao antiga nao sobrescreve a mais nova
    assert m2["situacao"] == "Parcial" and m2["achado"] == "texto novo"


def test_mescla_anexos_une_e_respeita_remocao():
    f = lambda i: {"nome": f"f{i}", "id_arquivo": f"id{i}", "link": f"http://x/{i}"}
    a = _d(anexos={"1": [f(1), f(2)]})
    b = _d(anexos={"1": [f(2), f(3)]}, removidos=["id1"])
    m = sb.mesclar_dados(a, b)
    assert [x["id_arquivo"] for x in m["anexos"]["1"]] == ["id2", "id3"]


def test_sessao_antiga_vazia_nao_apaga_visita(monkeypatch):
    """Cenario do ticket: outra aba/celular abriu a visita antes, ficou vazia e salvou depois."""
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    cheio = _d({"1": _r("OK", "19/10/2026 09:00:00"), "2": _r("OK", "19/10/2026 09:01:00")},
               anexos={"2": [{"nome": "a", "id_arquivo": "ia"}]})
    sb.salvar_rascunho("C1", "H", "R", cheio, 1000)
    sb.salvar_rascunho("C1", "H", "R", _d(visitados=[23, 0, 15]), 2000)
    gravado = _lido(aba)
    assert set(gravado["respostas"]) == {"1", "2"}
    assert gravado["anexos"]["2"][0]["id_arquivo"] == "ia"
    assert sb.mesclado_pendente("C1")["respostas"]
    assert sb.mesclado_pendente("C1") is None                  # entregue uma unica vez


def test_sem_diferenca_nao_gera_aviso(monkeypatch):
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    d = _d({"1": _r("OK", "19/10/2026 09:00:00")}, visitados=[1, 2])
    sb.salvar_rascunho("C3", "H", "R", d, 1)
    sb.salvar_rascunho("C3", "H", "R", dict(d, grupos_visitados=[1, 2]), 2)
    assert sb.mesclado_pendente("C3") is None


def test_versao_de_relogio_entre_sessoes_grava(monkeypatch):
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    sb.salvar_rascunho("C2", "H", "R", _d({"1": _r("OK", "19/10/2026 09:00:00")}), 1_000_000)
    sb.salvar_rascunho("C2", "H", "R", _d({"1": _r("OK", "19/10/2026 09:00:00"),
                                           "2": _r("OK", "19/10/2026 09:10:00")}), 2_000_000)
    assert set(_lido(aba)["respostas"]) == {"1", "2"}


def test_linha_movida_nao_sobrescreve_outra_visita(monkeypatch):
    """Cache de linha antigo (linhas apagadas na planilha) nao pode gravar na visita errada."""
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    sb.salvar_rascunho("A", "H", "R", _d({"1": _r("OK", "19/10/2026 09:00:00")}), 1)
    sb.salvar_rascunho("B", "H", "R", _d({"2": _r("OK", "19/10/2026 09:00:00")}), 1)
    aba.linhas.pop(1)                                           # apagaram a linha de A: B sobe
    sb.salvar_rascunho("B", "H", "R", _d({"2": _r("OK", "19/10/2026 09:00:00"),
                                          "3": _r("OK", "19/10/2026 09:02:00")}), 2)
    assert [l[0] for l in aba.linhas[1:]] == ["B"]
    assert set(_lido(aba)["respostas"]) == {"2", "3"}


def test_mescla_impactos_e_respostas_upa():
    g = {"respostas": {"1": {"resposta": "a", "atualizado_em": "19/10/2026 10:00:00"}}, "impactos": {"0": "x", "1": "y"}}
    n = {"respostas": {"1": {"resposta": "b", "atualizado_em": "19/10/2026 11:00:00"}, "2": {"resposta": "c"}}, "impactos": {"0": "x2"}}
    m = sb.mesclar_dados(g, n)
    assert m["respostas"]["1"]["resposta"] == "b" and "2" in m["respostas"]
    assert m["impactos"] == {"0": "x2", "1": "y"}


def test_registrar_anexo_grava_direto_no_rascunho_sem_sessao(monkeypatch):
    """Anexo enviado ao Drive e registrado no rascunho mesmo que a sessao do navegador tenha sumido."""
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    sb.salvar_rascunho("COD9", "Hosp", "Resp", _d(anexos={"1": [{"nome": "a.jpg", "id_arquivo": "A"}]}), 1)
    novo = {"nome": "b.jpg", "id_arquivo": "B", "link": "http://x/b"}
    assert sb.registrar_anexo_rascunho("COD9", 1, novo)
    assert sb.registrar_anexo_rascunho("COD9", 1, novo)          # repetido: nao duplica
    dados = _lido(aba)
    assert [a["id_arquivo"] for a in dados["anexos"]["1"]] == ["A", "B"]
    assert aba.linhas[1][1] == "Hosp" and aba.linhas[1][3] == "Resp"   # cabecalho preservado
    # um autosave antigo da sessao (sem a foto nova) nao a apaga
    sb.salvar_rascunho("COD9", "Hosp", "Resp", _d(anexos={"1": [{"nome": "a.jpg", "id_arquivo": "A"}]}), 2)
    assert [a["id_arquivo"] for a in _lido(aba)["anexos"]["1"]] == ["A", "B"]


def test_registrar_anexo_removido_nao_volta(monkeypatch):
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    sb.salvar_rascunho("COD8", "H", "R", _d(removidos=["B"]), 1)
    sb.registrar_anexo_rascunho("COD8", 1, {"nome": "b.jpg", "id_arquivo": "B"})
    assert not _lido(aba)["anexos"]


def test_registrar_anexo_sem_rascunho_nao_quebra(monkeypatch):
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    assert sb.registrar_anexo_rascunho("NAOEXISTE", 1, {"nome": "x", "id_arquivo": "X"}) is False
