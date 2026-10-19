"""Autosave: cache de aba/linha, agrupamento de rajadas e repeticao em erro 429."""
import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sheets_backend as sb


class AbaFalsa:
    def __init__(self, falhas_429=0):
        self.linhas = [["Codigo"]]
        self.leituras = 0
        self.gravacoes = 0
        self.falhas = falhas_429

    def col_values(self, n):
        self.leituras += 1
        return [l[0] for l in self.linhas]

    def get(self, rng):
        idx = int("".join(c for c in rng.split(":")[0] if c.isdigit()))
        return [self.linhas[idx - 1]] if idx - 1 < len(self.linhas) else []

    def update(self, rng, valores, value_input_option=None):
        if self.falhas > 0:
            self.falhas -= 1
            raise Exception("APIError: [429]: Quota exceeded for quota metric 'Read requests'")
        self.gravacoes += 1
        idx = int("".join(c for c in rng.split(":")[0] if c.isdigit()))
        self.linhas[idx - 1] = valores[0]

    def append_row(self, linha, value_input_option=None):
        self.gravacoes += 1
        self.linhas.append(linha)
        return {"updates": {"updatedRange": f"Rascunho!A{len(self.linhas)}:F{len(self.linhas)}"}}


def _preparar(aba, monkeypatch):
    sb._limpar_cache_rascunho()
    sb._ULTIMA_VERSAO.clear(); sb._PENDENTE.clear(); sb._ESCRITOR.clear(); sb._ULTIMA_GRAVACAO.clear()
    monkeypatch.setattr(sb, "_carregar_mapeamento", lambda: {})
    monkeypatch.setattr(sb, "_usa_google", lambda m: True)
    monkeypatch.setattr(sb, "_aba_rascunho", lambda: aba)
    monkeypatch.setattr(sb, "INTERVALO_MIN_GRAVACAO", 0)
    monkeypatch.setattr(sb, "ESPERAS_429", (0, 0, 0))


def test_leitura_da_linha_so_na_primeira_vez(monkeypatch):
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    for v in range(1, 8):
        sb.salvar_rascunho("COD1", "H", "R", {"v": v}, v)
    assert aba.leituras == 1, aba.leituras
    assert aba.linhas[1][5] == '{"v": 7}'
    assert sb.estado_autosave("COD1")["ok"]


def test_repete_em_429(monkeypatch):
    aba = AbaFalsa(falhas_429=2); _preparar(aba, monkeypatch)
    sb.salvar_rascunho("COD2", "H", "R", {"v": 1}, 1)
    assert sb.estado_autosave("COD2")["ok"], sb.estado_autosave("COD2")


def test_rajada_agrupa_e_grava_ultima(monkeypatch):
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    monkeypatch.setattr(sb, "INTERVALO_MIN_GRAVACAO", 0.3)
    ts = [threading.Thread(target=sb.salvar_rascunho, args=("COD3", "H", "R", {"v": v}, v)) for v in range(1, 21)]
    for t in ts: t.start()
    for t in ts: t.join()
    import time; time.sleep(0.8)
    assert aba.gravacoes <= 4, aba.gravacoes
    assert aba.linhas[1][5] == '{"v": 20}'


def test_envio_google_usa_gravacao_de_visita(monkeypatch):
    """Regressao: _gravar_google (envio) nao pode ser sobrescrita pela gravacao de rascunho."""
    class Aba:
        def __init__(self): self.linhas = []
        def col_values(self, n): return [l[0] for l in self.linhas]
        def append_rows(self, linhas, value_input_option=None): self.linhas += linhas
    abas = {}
    class Plan:
        def worksheet(self, t): return abas.setdefault(t, Aba())
    monkeypatch.setattr(sb, "_carregar_mapeamento", lambda: {})
    monkeypatch.setattr(sb, "_usa_google", lambda m: True)
    monkeypatch.setattr(sb, "_abrir_planilha", lambda: Plan())
    import schema as sc
    v = {c: "" for c in sc.COLUNAS_VISITA}; v["Código da Visita"] = "X-1"
    it = [{c: "" for c in sc.COLUNAS_ITEM}]; it[0]["Código da Visita"] = "X-1"
    try:
        sec = [{c: "" for c in sc.COLUNAS_SECAO}]; sec[0]["Código da Visita"] = "X-1"
        ok, modo, msg = sb.salvar_auditoria(v, it, [], sec)
    except TypeError:
        ok, modo, msg = sb.salvar_auditoria(v, it, [])
    assert ok and modo == "google_sheets", msg
    assert len(abas[sb.ABA_ITENS].linhas) == 1 if hasattr(sb, "ABA_ITENS") else True
    ok2, _, msg2 = sb.salvar_auditoria(v, it, [])
    assert ok2 and "nada foi duplicado" in msg2


def test_rascunho_grande_e_dividido_em_blocos(monkeypatch):
    """Rascunho acima de 50.000 caracteres (muitos anexos) vai em varias celulas e volta inteiro."""
    aba = AbaFalsa(); _preparar(aba, monkeypatch)
    grande = {"anexos": {str(i): [{"nome": "x" * 200, "link": "y" * 100} for _ in range(20)] for i in range(1, 40)}}
    import json
    texto = json.dumps(grande, ensure_ascii=False)
    assert len(texto) > 100000
    sb.salvar_rascunho("COD9", "H", "R", grande, 1)
    assert sb.estado_autosave("COD9")["ok"], sb.estado_autosave("COD9")
    linha = aba.linhas[1]
    assert all(len(c) <= 40000 for c in linha[5:]) and len(linha) == 5 + sb.BLOCOS_RASCUNHO
    assert "".join(linha[5:]) == texto
    # rascunho menor depois: blocos antigos sao limpos
    sb.salvar_rascunho("COD9", "H", "R", {"v": 1, "anexos_removidos": ["y" * 100]}, 2)
    assert json.loads("".join(aba.linhas[1][5:])) == {"v": 1, "anexos_removidos": ["y" * 100], "anexos": {}}
    assert all(c == "" for c in aba.linhas[1][7:])
