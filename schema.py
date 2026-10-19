# -*- coding: utf-8 -*-
"""
schema.py - Checklist de Visita Tecnica para UPA (Sao Lucas Instituto) - 11 secoes / 107 itens

Catalogo de grupos e itens + constantes + colunas das planilhas.

IMPORTANTE: o ID do item (001..107, igual ao formulario) e a CHAVE ESTAVEL que liga os dados
historicos ao catalogo. Nunca renumere; itens novos recebem IDs novos (depois do ultimo).
"""
import re
import unicodedata
from datetime import datetime, timedelta, timezone

UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]

FUSO_BRASILIA = timezone(timedelta(hours=-3))

# Fonte da informacao (resposta do formulario). "Verificado" (caixa OK do formulario) = as tres primeiras.
OBSERVADO = "Observado"
INFORMADO = "Informado"
OBS_INF = "Observado e informado"
NAO_VERIF = "Não verificado"
NAO_SE_APLICA = "Não se aplica"
OPCOES_FONTE = [OBSERVADO, INFORMADO, OBS_INF, NAO_VERIF, NAO_SE_APLICA]
FONTES_VERIFICADAS = (OBSERVADO, INFORMADO, OBS_INF)
ESSENCIAL, COMPLEMENTAR = "E", "C"
ROTULO_FOCO = {ESSENCIAL: "Essencial", COMPLEMENTAR: "Complementar"}

# Limites de anexo (evidencia)
EXTENSOES_PERMITIDAS = ["jpg", "jpeg", "png", "pdf"]
MAX_ANEXOS_POR_ITEM = 20
MAX_MB_IMAGEM_ENTRADA = 20
MAX_MB_PDF = 10
LADO_MAX_IMAGEM_PX = 1600
QUALIDADE_JPEG = 80

# (numero da secao, nome, [(ID, foco E/C, pergunta ou dado a levantar), ...])
# Fonte: CHECKLIST_VISITA_TECNICA_UPA (roteiro revisado). O nome da unidade NAO faz parte do catalogo.
GRUPOS_BRUTOS = [
    (1, 'Perfil e demanda', [
        (1, 'E', 'Perfil real: urgência e observação ou permanência prolongada com cuidados contínuos?'),
        (2, 'E', 'Atendimentos diários aproximados (atendimentos/dia)'),
        (3, 'E', 'Horários e dias de maior movimento e sazonalidade'),
        (4, 'E', 'Perfil predominante e distribuição entre adultos e crianças'),
        (5, 'E', 'Leitos de observação existentes (leitos)'),
        (6, 'E', 'Leitos ocupados na visita (leitos)'),
        (7, 'E', 'Leitos de isolamento (leitos)'),
        (8, 'E', 'Poltronas de medicação (poltronas)'),
        (9, 'E', 'Pacientes há mais de 24 horas na unidade (pacientes)'),
        (10, 'E', 'Maior permanência informada (dias)'),
        (11, 'E', 'Motivos da permanência e cuidados contínuos exigidos'),
        (12, 'E', 'Principal etapa em que a fila acumula e causa da demora'),
    ]),
    (2, 'Emergência', [
        (13, 'E', 'Capacidade simultânea da sala de emergência (vagas)'),
        (14, 'E', 'Pacientes na emergência durante a visita (pacientes)'),
        (15, 'E', 'Pacientes ventilados durante a visita (pacientes)'),
        (16, 'E', 'Monitores disponíveis e condição de funcionamento'),
        (17, 'E', 'Ventiladores disponíveis e condição de funcionamento'),
        (18, 'E', 'Desfibriladores disponíveis e condição de funcionamento'),
        (19, 'E', 'Bombas de infusão disponíveis e condição de funcionamento'),
        (20, 'E', 'Oxigênio, aspiração, carro de emergência e material de via aérea disponíveis?'),
        (21, 'E', 'Equipe da emergência por turno; é exclusiva ou também atende a fila?'),
        (22, 'E', 'Equipamento parado ou limitação que compromete o atendimento'),
    ]),
    (3, 'Ambientes e segurança', [
        (23, 'C', 'Consultórios em uso e salas de medicação, sutura, procedimentos e gesso'),
        (24, 'C', 'Odontologia e separação dos fluxos adulto e pediátrico'),
        (25, 'C', 'Identificação dos pacientes, isolamento e acomodação de pacientes em crise de saúde mental'),
        (26, 'C', 'Gargalos visíveis no fluxo ou acomodação de pacientes'),
    ]),
    (4, 'Diagnóstico', [
        (27, 'C', 'Laboratório: coleta ou processamento local? Próprio, externo ou misto?'),
        (28, 'C', 'Laboratório: exames urgentes disponíveis e limitações'),
        (29, 'C', 'Laboratório: horário real, cobertura noturna e fins de semana'),
        (30, 'C', 'Laboratório: prazo de resultado, transporte, equipe e fornecedor'),
        (31, 'C', 'RX: local ou externo; equipamento fixo/móvel e funcionamento'),
        (32, 'C', 'RX: técnicos por turno, laudo, prazo e fornecedor'),
        (33, 'C', 'ECG: local/externo e horário de disponibilidade'),
        (34, 'C', 'Ultrassom: local/externo, horário e profissional disponível'),
        (35, 'C', 'Gasometria: disponibilidade, local e horário'),
        (36, 'C', 'Tomografia e outros exames: referência, transporte e prazo'),
        (37, 'C', 'Responsabilidade informada pelos equipamentos, insumos e custeio dos exames'),
    ]),
    (5, 'Cozinha e alimentação', [
        (38, 'C', 'Produção local ou recebimento, aquecimento e distribuição?'),
        (39, 'C', 'Quantidade estimada de refeições (refeições/dia)'),
        (40, 'C', 'Pacientes, acompanhantes e trabalhadores atendidos; dietas especiais'),
        (41, 'C', 'Fornecedor, equipe, horários e estrutura em uso'),
        (42, 'C', 'O serviço permanece na transição? Necessidade de contratação imediata?'),
    ]),
    (6, 'Lavanderia e enxoval', [
        (43, 'C', 'Lavagem local, terceirizada ou rede municipal? Há somente rouparia?'),
        (44, 'C', 'Fornecedor, frequência de coleta/entrega e volume estimado'),
        (45, 'C', 'Reserva de roupa limpa, faltas e responsável pela reposição'),
        (46, 'C', 'Separação e armazenamento de roupa limpa e suja'),
        (47, 'C', 'Enxoval e serviço permanecerão na transição?'),
    ]),
    (7, 'Apoio operacional', [
        (48, 'C', 'Esterilização: local/externa, autoclave em uso, fornecedor e reserva'),
        (49, 'C', 'Farmácia: abastecimento, faltas e acesso aos medicamentos à noite'),
        (50, 'C', 'Estoque inicial: itens que ficarão e duração estimada'),
        (51, 'C', 'Gases: fornecimento, reserva e responsável pelo custo'),
        (52, 'C', 'Gerador: funcionamento informado e setores atendidos'),
        (53, 'C', 'Manutenção, climatização, infiltrações e equipamentos parados'),
        (54, 'C', 'Limpeza e resíduos: modelo, fornecedor, insumos e armazenamento'),
        (55, 'C', 'Profissionais de limpeza no plantão diurno (profissionais)'),
        (56, 'C', 'Profissionais de limpeza no plantão noturno (profissionais)'),
        (57, 'C', 'Duração do plantão de limpeza e cobertura em fins de semana/feriados'),
    ]),
    (8, 'Remoção e regulação', [
        (58, 'E', 'Ambulância exclusiva, tipo, equipe, cobertura e responsável pelo custeio'),
        (59, 'E', 'Equipe da remoção exclusiva ou retirada da assistência interna?'),
        (60, 'E', 'Referência principal e município'),
        (61, 'E', 'Distância até a referência somente ida (km)'),
        (62, 'E', 'Distância total de ida e volta (km)'),
        (63, 'E', 'Tempo aproximado de ida (minutos)'),
        (64, 'E', 'Outras referências e distâncias'),
        (65, 'E', 'Número de viagens no período informado (viagens)'),
        (66, 'E', 'Período a que se refere o número de viagens (dia, mês ou intervalo)'),
        (67, 'E', 'Valor informado da remoção (R$)'),
        (68, 'E', 'Base do valor (viagem, km, mensal ou outra) e tipo de serviço'),
        (69, 'E', 'Valor inclui equipe, combustível, retorno e espera?'),
        (70, 'E', 'Espera habitual por vaga e principal obstáculo à transferência'),
        (71, 'E', 'Tempo e fluxo entre decisão médica e solicitação à regulação'),
    ]),
    (9, 'Equipe e plantões', [
        (72, 'C', 'Médicos por turno e especialidade; distribuição entre fila, emergência e observação'),
        (73, 'C', 'Enfermeiros e técnicos por turno e setor; cobertura de faltas'),
        (74, 'C', 'Especialidade médica 1'),
        (75, 'C', 'Duração do plantão médico da especialidade 1 (horas)'),
        (76, 'C', 'Valor diurno por profissional e plantão da especialidade 1 (R$)'),
        (77, 'C', 'Valor noturno por profissional e plantão da especialidade 1 (R$)'),
        (78, 'C', 'Especialidade médica 2'),
        (79, 'C', 'Duração do plantão médico da especialidade 2 (horas)'),
        (80, 'C', 'Valor diurno por profissional e plantão da especialidade 2 (R$)'),
        (81, 'C', 'Valor noturno por profissional e plantão da especialidade 2 (R$)'),
        (82, 'C', 'Especialidade médica 3'),
        (83, 'C', 'Duração do plantão médico da especialidade 3 (horas)'),
        (84, 'C', 'Valor diurno por profissional e plantão da especialidade 3 (R$)'),
        (85, 'C', 'Valor noturno por profissional e plantão da especialidade 3 (R$)'),
        (86, 'C', 'Diferença de valores em fins de semana/feriados e forma de contratação'),
        (87, 'C', 'Recepcionistas por plantão diurno (profissionais)'),
        (88, 'C', 'Recepcionistas por plantão noturno (profissionais)'),
        (89, 'C', 'Duração do plantão da recepção e cobertura em fins de semana/feriados'),
        (90, 'C', 'Servidores municipais e demais profissionais: quem poderá permanecer? O que precisa de confirmação?'),
    ]),
    (10, 'Sistemas e indicadores', [
        (91, 'C', 'Prontuário, internet, computadores e manutenção do acesso na transição'),
        (92, 'C', 'Registro de horários de chegada, classificação, consulta, exames e transferência'),
        (93, 'C', 'Extração de dados de produção, permanência, retornos e satisfação'),
        (94, 'C', 'Dificuldade atual para medir ou cumprir indicadores; causa interna ou dependência externa?'),
    ]),
    (11, 'Transição e decisão', [
        (95, 'E', 'Bens do Município, da gestora e de fornecedores; quais poderão ser retirados?'),
        (96, 'E', 'Contratos e serviços essenciais cuja continuidade precisa ser confirmada'),
        (97, 'E', 'Principal dificuldade da unidade segundo o acompanhante'),
        (98, 'E', 'Impacto dessa dificuldade no atendimento e na operação'),
        (99, 'E', 'Se pudesse resolver uma única questão imediatamente, qual seria?'),
        (100, 'E', 'Principal achado observado pela equipe São Lucas'),
        (101, 'E', 'Três maiores riscos para assumir a operação'),
        (102, 'E', 'Compras, adequações e contratações prioritárias'),
        (103, 'E', 'Responsabilidades ou custos ainda sem definição'),
        (104, 'E', 'Esclarecimentos a encaminhar à Secretaria'),
        (105, 'E', 'Providências recomendadas para o primeiro dia de operação'),
        (106, 'E', 'Providências recomendadas para os primeiros 30 dias'),
        (107, 'E', 'Providências recomendadas para 60 e 90 dias'),
    ]),
]

import re as _re

GRUPOS = []
for _num_sec, _nome, _itens in GRUPOS_BRUTOS:
    _lista = []
    for _id, _foco, _texto in _itens:
        _un = _re.search(r"\(([^()]+)\)\s*$", _texto)
        _lista.append({"num": _id, "ref": f"{_id:03d}", "foco": _foco, "texto": _texto,
                       "unidade": _un.group(1) if _un else ""})
    GRUPOS.append({"nome": f"{_num_sec}. {_nome}", "foco": _lista[0]["foco"], "itens": _lista})

TOTAL_ITENS = sum(len(g["itens"]) for g in GRUPOS)
TOTAL_ESSENCIAIS = sum(1 for g in GRUPOS for i in g["itens"] if i["foco"] == ESSENCIAL)
TOTAL_COMPLEMENTARES = TOTAL_ITENS - TOTAL_ESSENCIAIS

COLUNAS_VISITA = [
    "Código da Visita", "Unidade", "Cidade", "UF", "Edital / Processo", "Data da Visita", "Horário",
    "Visitantes", "Acompanhante / função", "Início do Preenchimento", "Fim do Preenchimento (Envio)",
    "Status da Visita", "Total de Itens", "Itens Respondidos", "Essenciais Respondidos", "Complementares Respondidos",
    "Total Verificados", "Total Não Verificados", "Total Não se Aplica", "Total Não Preenchido",
    "Total de Anexos", "Seções com Impacto Registrado",
]

COLUNAS_ITEM = [
    "Código da Visita", "Unidade", "Data da Visita", "Seção", "ID", "Foco",
    "Pergunta ou dado a levantar", "Resposta / valor", "Fonte", "Verificado (OK)", "Observação",
    "Qtde de Anexos", "Respondido em",
]

COLUNAS_SECAO = [
    "Código da Visita", "Unidade", "Nº da Seção", "Seção", "Impacto na proposta e providências São Lucas",
]

COLUNAS_EVIDENCIA = [
    "Código da Visita", "Unidade", "ID", "Ref.", "Arquivo", "Tipo",
    "Tamanho (KB)", "Enviado em", "Link / Caminho",
]


def agora_brasilia() -> datetime:
    return datetime.now(FUSO_BRASILIA)


def chave_hospital(nome: str) -> str:
    """Chave de comparacao do nome do hospital: sem acentos, minuscula e sem
    espacos repetidos - 'Hospital  Sao Jose' == 'hospital são josé'."""
    nfkd = unicodedata.normalize("NFKD", nome or "")
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().casefold()


def sigla_hospital(nome: str) -> str:
    """Ate 8 letras/numeros maiusculos para compor o codigo da visita."""
    nfkd = unicodedata.normalize("NFKD", nome or "")
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    palavras = [p for p in re.split(r"[^A-Za-z0-9]+", sem_acento) if p and p.lower() not in ("de", "da", "do", "das", "dos", "e")]
    base = "".join(p[0] for p in palavras)[:6] or "HOSP"
    return base.upper()


def gerar_codigo_visita(hospital: str) -> str:
    """Formato: UPA-<SIGLA>-<AAAAMMDD>-<4 hex> (ex.: UPA-SUL-20261020-A3F9)."""
    import uuid
    return f"UPA-{sigla_hospital(hospital)}-{agora_brasilia().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
