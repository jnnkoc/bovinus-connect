"""Bovinu's Connect — servidor e API REST (somente biblioteca padrão)."""
import csv
import hashlib
import hmac
import io
import json
import threading
from http.cookies import CookieError, SimpleCookie
import mimetypes
import os
import re
import secrets
import socket
import sys
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date, datetime, time, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

PASTA = Path(__file__).resolve().parent
BANCO = Path(os.environ.get("BOVINUS_BANCO", PASTA / "bovinus.db"))
VERSAO_BANCO = 2

# São Paulo não tem horário de verão desde 2019: UTC-3 fixo (evita depender de tzdata no Windows).
SP = timezone(timedelta(hours=-3), "America/Sao_Paulo")

ALFABETO = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # sem 0/O e 1/I
CODIGO = re.compile(rf"BOV-[{ALFABETO}]{{4}}")
CATEGORIAS = ("churrasco", "acompanhamento", "salada", "sobremesa")
MAX_PRATOS_INTENCAO = 3
LIMITE_VISITA = timedelta(hours=3)        # visita aberta além disso é fechada com saída estimada
TOLERANCIA_CHEGADA = timedelta(minutes=30)  # intenção sem check-in após previsto + 30 min = não convertida
FAIXA = timedelta(minutes=15)

PAGINAS = {
    "/": "cliente.html",
    "/cliente": "cliente.html",
    "/avaliar": "avaliar.html",
    "/terminal": "terminal.html",
    "/cardapio": "cardapio.html",
    "/dashboard": "dashboard.html",
}
PAGINAS["/login"] = "login.html"
# Telas da equipe exigem login; o valor diz quais papéis podem abrir.
GERENTE = ("gerente",)
EQUIPE = ("gerente", "atendente")
PAGINAS_EQUIPE = {"terminal.html": EQUIPE, "cardapio.html": GERENTE, "dashboard.html": GERENTE}
COOKIE = "bovinus_sessao"
DURACAO_SESSAO = timedelta(hours=12)
ITERACOES_SENHA = 200_000
MAX_FALHAS_LOGIN = 5
BLOQUEIO_LOGIN = timedelta(minutes=5)
ARQUIVOS = {"estilo.css", "comum.js"}
PASTAS_ESTATICAS = ("img", "vendor")


class ErroAPI(Exception):
    def __init__(self, status, mensagem):
        self.status = status
        super().__init__(mensagem)


# ---------------------------------------------------------------- utilidades de tempo

def agora():
    return datetime.now(timezone.utc)


def iso(momento):
    return momento.astimezone(timezone.utc).isoformat(timespec="milliseconds")


def ler_iso(texto):
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def hoje_local():
    return agora().astimezone(SP).date()


def inicio_dia(dia):
    return datetime.combine(dia, time(), SP)


def limites_dia(dia):
    return iso(inicio_dia(dia)), iso(inicio_dia(dia + timedelta(days=1)))


def dia_local(texto):
    return ler_iso(texto).astimezone(SP).date()


def ler_data(texto, padrao=None):
    if not texto:
        return padrao or hoje_local()
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ErroAPI(400, "Data inválida. Use AAAA-MM-DD.")


def minutos(inicio, fim):
    return (ler_iso(fim) - ler_iso(inicio)).total_seconds() / 60


def media(valores):
    valores = list(valores)
    return round(sum(valores) / len(valores), 1) if valores else None


def calcular_nps(notas):
    notas = list(notas)
    if not notas:
        return None
    promotores = sum(n >= 9 for n in notas)
    detratores = sum(n <= 6 for n in notas)
    return round(100 * (promotores - detratores) / len(notas))


def pct(parte, total):
    return round(100 * parte / total) if total else None


def br(numero, casas=1):
    return f"{numero:.{casas}f}".replace(".", ",")


def hhmm(momento):
    texto = momento.astimezone(SP).strftime("%Hh%M")
    return texto[:-2] if texto.endswith("00") else texto


# ---------------------------------------------------------------- banco

def conectar():
    banco = sqlite3.connect(BANCO, timeout=10)
    banco.row_factory = sqlite3.Row
    banco.execute("PRAGMA foreign_keys = ON")
    return banco


def preparar_banco(criar_usuarios=True):
    """Cria o banco. Um banco da versão antiga é guardado como .bak e recriado.
    Sem nenhum usuário, cria 'gerente' e 'atendente' com senha aleatória e mostra no terminal."""
    if BANCO.exists():
        with closing(sqlite3.connect(BANCO)) as banco:
            versao = banco.execute("PRAGMA user_version").fetchone()[0]
            tem_tabelas = banco.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        if tem_tabelas and versao < VERSAO_BANCO:
            reserva = BANCO.with_suffix(".db.v1.bak")
            BANCO.replace(reserva)
            print(f"Banco antigo movido para {reserva.name}; criando banco novo.", flush=True)
    with closing(conectar()) as banco:
        banco.executescript((PASTA / "schema.sql").read_text(encoding="utf-8"))
        if criar_usuarios and not banco.execute("SELECT COUNT(*) FROM usuario").fetchone()[0]:
            print("Nenhum usuário da equipe encontrado. Criados agora (anote as senhas):", flush=True)
            with banco:
                for login, nome, papel in (("gerente", "Gerente", "gerente"), ("atendente", "Atendente", "atendente")):
                    senha = os.environ.get(f"BOVINUS_SENHA_{login.upper()}") or secrets.token_urlsafe(9)
                    criar_usuario(banco, login, nome, papel, senha)
                    print(f"  {login} ({papel}): {senha}", flush=True)
            print("Para trocar: py usuarios.py senha <login>", flush=True)


# ---------------------------------------------------------------- equipe e sessão

def hash_senha(senha, sal=None, iteracoes=ITERACOES_SENHA):
    sal = sal or secrets.token_hex(16)
    calculado = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal), iteracoes).hex()
    return f"pbkdf2_sha256${iteracoes}${sal}${calculado}"


def conferir_senha(senha, armazenado):
    try:
        _, iteracoes, sal, _ = armazenado.split("$")
        return hmac.compare_digest(hash_senha(senha, sal, int(iteracoes)), armazenado)
    except ValueError:
        return False


def validar_senha(senha):
    if not isinstance(senha, str) or len(senha) < 8:
        raise ErroAPI(400, "A senha precisa ter pelo menos 8 caracteres.")


def criar_usuario(banco, login, nome, papel, senha):
    validar_senha(senha)
    if papel not in EQUIPE:
        raise ErroAPI(400, "Papel inválido. Use gerente ou atendente.")
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,30}", login):
        raise ErroAPI(400, "Login: 3 a 30 letras, números, ponto, hífen ou sublinhado.")
    banco.execute("INSERT INTO usuario (login, nome, papel, senha_hash) VALUES (?, ?, ?, ?)",
                  (login, nome, papel, hash_senha(senha)))


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


_falhas_login = {}
_trava_falhas = threading.Lock()


def entrar(banco, dados, ip):
    login = str(dados.get("login", "")).strip().lower()
    senha = dados.get("senha", "")
    chave = (ip, login)
    with _trava_falhas:
        falhas, ate = _falhas_login.get(chave, (0, None))
        if ate and agora() < ate:
            raise ErroAPI(429, "Muitas tentativas. Aguarde alguns minutos e tente de novo.")
    usuario = banco.execute("SELECT * FROM usuario WHERE login = ? AND ativo = 1", (login,)).fetchone()
    if usuario is None or not isinstance(senha, str) or not conferir_senha(senha, usuario["senha_hash"]):
        with _trava_falhas:
            falhas += 1
            _falhas_login[chave] = (0, agora() + BLOQUEIO_LOGIN) if falhas >= MAX_FALHAS_LOGIN else (falhas, None)
        raise ErroAPI(401, "Login ou senha incorretos.")
    with _trava_falhas:
        _falhas_login.pop(chave, None)
    banco.execute("DELETE FROM sessao WHERE expira_em < ?", (iso(agora()),))
    token = secrets.token_urlsafe(32)
    banco.execute("INSERT INTO sessao (token_hash, usuario_id, criada_em, expira_em) VALUES (?, ?, ?, ?)",
                  (hash_token(token), usuario["id"], iso(agora()), iso(agora() + DURACAO_SESSAO)))
    return token, {"login": usuario["login"], "nome": usuario["nome"], "papel": usuario["papel"]}


def usuario_da_sessao(banco, token):
    if not token:
        return None
    linha = banco.execute(
        """SELECT u.login, u.nome, u.papel FROM sessao s JOIN usuario u ON u.id = s.usuario_id
           WHERE s.token_hash = ? AND s.expira_em > ? AND u.ativo = 1""",
        (hash_token(token), iso(agora()))).fetchone()
    return dict(linha) if linha else None


def papeis_exigidos(metodo, partes):
    """Quem pode chamar cada rota da API. None = pública (app do cliente)."""
    if not partes:
        return None
    if partes[0] == "cardapio" and metodo != "GET":
        return GERENTE
    if partes[0] in ("dashboard", "visitas.csv", "clientes"):
        return GERENTE
    if partes == ["visitas"] or (partes[0] == "jornadas" and partes[-1] == "proxima" and len(partes) == 3):
        return EQUIPE
    return None


def fechar_visitas_antigas(banco):
    """Visita sem check-out após 3 h é fechada com saida_estimada = 1."""
    limite = iso(agora() - LIMITE_VISITA)
    abertas = banco.execute(
        "SELECT id, check_in_em FROM visita WHERE check_out_em IS NULL AND check_in_em < ?", (limite,)
    ).fetchall()
    for visita in abertas:
        banco.execute(
            "UPDATE visita SET check_out_em = ?, saida_estimada = 1 WHERE id = ?",
            (iso(ler_iso(visita["check_in_em"]) + LIMITE_VISITA), visita["id"]),
        )


def gerar_codigo(banco):
    for _ in range(50):
        codigo = "BOV-" + "".join(secrets.choice(ALFABETO) for _ in range(4))
        existe = banco.execute(
            "SELECT 1 FROM intencao WHERE codigo = ? UNION SELECT 1 FROM visita WHERE codigo = ?",
            (codigo, codigo),
        ).fetchone()
        if not existe:
            return codigo
    raise ErroAPI(503, "Não foi possível gerar o código. Tente novamente.")


def normalizar_codigo(texto):
    """Aceita 'BOV-ABCD', 'bov abcd' ou só 'ABCD'."""
    limpo = re.sub(r"[^0-9A-Z]", "", unquote(texto).upper())
    if limpo.startswith("BOV"):
        limpo = limpo[3:]
    codigo = "BOV-" + limpo
    if not CODIGO.fullmatch(codigo):
        raise ErroAPI(400, "Código inválido. Use o formato BOV-XXXX.")
    return codigo


def simulado(banco):
    linha = banco.execute("SELECT valor FROM parametro WHERE chave = 'dados_simulados'").fetchone()
    return bool(linha and linha["valor"] == "1")


# ---------------------------------------------------------------- cardápio

def listar_cardapio(banco, dia):
    linhas = banco.execute(
        """SELECT p.id, p.nome, p.categoria, p.descricao, p.vegetariano, c.destaque
           FROM cardapio_dia c JOIN prato p ON p.id = c.prato_id
           WHERE c.data = ?
           ORDER BY CASE p.categoria WHEN 'churrasco' THEN 1 WHEN 'acompanhamento' THEN 2
                    WHEN 'salada' THEN 3 ELSE 4 END, c.destaque DESC, p.nome""",
        (dia.isoformat(),),
    )
    pratos = [dict(l, vegetariano=bool(l["vegetariano"]), destaque=bool(l["destaque"])) for l in linhas]
    return {"data": dia.isoformat(), "pratos": pratos}


def validar_prato(dados):
    nome = str(dados.get("nome", "")).strip()
    categoria = dados.get("categoria")
    descricao = str(dados.get("descricao", "")).strip()
    if not 2 <= len(nome) <= 60:
        raise ErroAPI(400, "Informe o nome do prato (2 a 60 caracteres).")
    if categoria not in CATEGORIAS:
        raise ErroAPI(400, "Categoria inválida.")
    if len(descricao) > 120:
        raise ErroAPI(400, "A descrição deve ter até 120 caracteres.")
    return nome, categoria, descricao, int(bool(dados.get("vegetariano"))), int(bool(dados.get("destaque")))


def adicionar_prato(banco, dia, dados):
    nome, categoria, descricao, vegetariano, destaque = validar_prato(dados)
    existente = banco.execute(
        "SELECT id FROM prato WHERE lower(nome) = lower(?) AND categoria = ?", (nome, categoria)
    ).fetchone()
    if existente:
        prato_id = existente["id"]
        banco.execute(
            "UPDATE prato SET nome = ?, descricao = ?, vegetariano = ? WHERE id = ?",
            (nome, descricao, vegetariano, prato_id),
        )
    else:
        prato_id = banco.execute(
            "INSERT INTO prato (nome, categoria, descricao, vegetariano) VALUES (?, ?, ?, ?)",
            (nome, categoria, descricao, vegetariano),
        ).lastrowid
    inserido = banco.execute(
        "INSERT INTO cardapio_dia (data, prato_id, destaque) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
        (dia.isoformat(), prato_id, destaque),
    ).rowcount
    if not inserido:
        raise ErroAPI(409, "Este prato já está no cardápio do dia.")
    return 201, listar_cardapio(banco, dia)


def editar_prato(banco, dia, prato_id, dados):
    nome, categoria, descricao, vegetariano, destaque = validar_prato(dados)
    alterado = banco.execute(
        "UPDATE cardapio_dia SET destaque = ? WHERE data = ? AND prato_id = ?",
        (destaque, dia.isoformat(), prato_id),
    ).rowcount
    if not alterado:
        raise ErroAPI(404, "Prato não encontrado no cardápio deste dia.")
    banco.execute(
        "UPDATE prato SET nome = ?, categoria = ?, descricao = ?, vegetariano = ? WHERE id = ?",
        (nome, categoria, descricao, vegetariano, prato_id),
    )
    return 200, listar_cardapio(banco, dia)


def remover_prato(banco, dia, prato_id):
    removido = banco.execute(
        "DELETE FROM cardapio_dia WHERE data = ? AND prato_id = ?", (dia.isoformat(), prato_id)
    ).rowcount
    if not removido:
        raise ErroAPI(404, "Prato não encontrado no cardápio deste dia.")
    return 200, listar_cardapio(banco, dia)


def copiar_cardapio_anterior(banco, dia):
    anterior = banco.execute(
        "SELECT MAX(data) AS data FROM cardapio_dia WHERE data < ?", (dia.isoformat(),)
    ).fetchone()["data"]
    if not anterior:
        raise ErroAPI(404, "Não há cardápio anterior para copiar.")
    banco.execute(
        """INSERT INTO cardapio_dia (data, prato_id, destaque)
           SELECT ?, prato_id, destaque FROM cardapio_dia WHERE data = ? ON CONFLICT DO NOTHING""",
        (dia.isoformat(), anterior),
    )
    resultado = listar_cardapio(banco, dia)
    resultado["copiado_de"] = anterior
    return 200, resultado


# ---------------------------------------------------------------- jornada

def buscar_jornada(banco, codigo):
    linha = banco.execute("SELECT * FROM jornada WHERE codigo = ?", (codigo,)).fetchone()
    if linha is None:
        raise ErroAPI(404, "Código não encontrado.")
    return dict(linha)


def visitas_do_cliente(banco, cliente_id):
    if cliente_id is None:
        return None
    return banco.execute(
        "SELECT COUNT(*) FROM visita WHERE cliente_id = ? AND check_out_em IS NOT NULL", (cliente_id,)
    ).fetchone()[0]


def consultar(banco, codigo):
    """Visão pública da visita: status, sem dados pessoais."""
    j = buscar_jornada(banco, codigo)
    pratos = []
    if j["intencao_id"]:
        pratos = [l["nome"] for l in banco.execute(
            """SELECT p.nome FROM intencao_prato ip JOIN prato p ON p.id = ip.prato_id
               WHERE ip.intencao_id = ? ORDER BY p.nome""", (j["intencao_id"],))]
    if j["check_out_em"]:
        status = "encerrada"
    elif j["check_in_em"]:
        status = "em_andamento"
    else:
        status = "aguardando"
    return {
        "codigo": j["codigo"],
        "origem": j["origem"],
        "status": status,
        "horario_previsto": j["horario_previsto"],
        "pessoas": j["pessoas"],
        "pratos": pratos,
        "check_in_em": j["check_in_em"],
        "buffet_concluido_em": j["buffet_concluido_em"],
        "check_out_em": j["check_out_em"],
        "saida_estimada": bool(j["saida_estimada"]),
        "mesa": j["mesa"],
        "avaliada": j["nota_nps"] is not None,
        "visitas_cliente": visitas_do_cliente(banco, j["cliente_id"]),
    }


def criar_intencao(banco, dados):
    try:
        previsto = ler_iso(str(dados["horario_previsto"]))
        if previsto.utcoffset() is None:
            raise ValueError
    except (KeyError, ValueError, OverflowError):
        raise ErroAPI(400, "Informe horario_previsto em formato ISO com fuso horário.")
    if previsto < agora() - timedelta(minutes=15):
        raise ErroAPI(400, "O horário previsto já passou.")
    if previsto > agora() + timedelta(days=7):
        raise ErroAPI(400, "Planeje visitas para os próximos 7 dias.")

    pessoas = dados.get("pessoas", 1)
    if type(pessoas) is not int or not 1 <= pessoas <= 20:
        raise ErroAPI(400, "Informe de 1 a 20 pessoas.")

    pratos = dados.get("pratos", [])
    if not isinstance(pratos, list) or any(type(p) is not int for p in pratos):
        raise ErroAPI(400, "Envie os pratos como uma lista de ids.")
    pratos = list(dict.fromkeys(pratos))
    if len(pratos) > MAX_PRATOS_INTENCAO:
        raise ErroAPI(400, f"Escolha até {MAX_PRATOS_INTENCAO} pratos de interesse.")
    dia = previsto.astimezone(SP).date()
    if pratos:
        no_dia = {l["prato_id"] for l in banco.execute(
            "SELECT prato_id FROM cardapio_dia WHERE data = ?", (dia.isoformat(),))}
        if not set(pratos) <= no_dia:
            raise ErroAPI(400, "Algum prato escolhido não está no cardápio desse dia.")

    nome = str(dados.get("nome", "")).strip()
    celular = re.sub(r"\D", "", str(dados.get("celular", "")))
    if not 2 <= len(nome) <= 80:
        raise ErroAPI(400, "Informe seu nome.")
    if len(celular) not in (10, 11):
        raise ErroAPI(400, "Informe o celular com DDD.")
    if dados.get("aceite_lgpd") is not True:
        raise ErroAPI(400, "É preciso aceitar o uso dos dados para planejar a visita.")

    momento = iso(agora())
    banco.execute(
        """INSERT INTO cliente (nome, celular, consentimento_em) VALUES (?, ?, ?)
           ON CONFLICT(celular) DO UPDATE SET nome = excluded.nome, consentimento_em = excluded.consentimento_em""",
        (nome, celular, momento),
    )
    cliente_id = banco.execute("SELECT id FROM cliente WHERE celular = ?", (celular,)).fetchone()["id"]
    codigo = gerar_codigo(banco)
    intencao_id = banco.execute(
        """INSERT INTO intencao (codigo, cliente_id, horario_previsto, pessoas, criada_em)
           VALUES (?, ?, ?, ?, ?)""",
        (codigo, cliente_id, iso(previsto), pessoas, momento),
    ).lastrowid
    banco.executemany(
        "INSERT INTO intencao_prato (intencao_id, prato_id) VALUES (?, ?)",
        [(intencao_id, p) for p in pratos],
    )
    return 201, consultar(banco, codigo)


def criar_visita_espontanea(banco):
    codigo = gerar_codigo(banco)
    banco.execute(
        "INSERT INTO visita (codigo, origem, check_in_em) VALUES (?, 'espontaneo', ?)",
        (codigo, iso(agora())),
    )
    return 201, consultar(banco, codigo)


def registrar_proxima(banco, codigo, dados):
    """Registra a etapa que cabe ao modo do terminal. Ninguém escolhe a etapa."""
    modo = dados.get("modo")
    if modo not in ("entrada", "balanca", "caixa"):
        raise ErroAPI(400, "Modo inválido. Use entrada, balanca ou caixa.")
    j = buscar_jornada(banco, codigo)
    momento = iso(agora())

    def resposta(etapa, campo, repetido, mensagem):
        visita = consultar(banco, codigo)
        return 200, {"etapa": etapa, "repetido": repetido, "horario": visita[campo],
                     "mensagem": mensagem, "visita": visita}

    if j["check_out_em"] and not (modo == "caixa" and j["saida_estimada"]):
        if modo == "caixa":
            return resposta("check-out", "check_out_em", True, "Saída já registrada.")
        raise ErroAPI(409, "Esta visita já foi encerrada.")

    if modo == "entrada":
        if j["visita_id"]:
            return resposta("check-in", "check_in_em", True, "Check-in já registrado.")
        banco.execute(
            """INSERT INTO visita (codigo, origem, intencao_id, cliente_id, check_in_em)
               VALUES (?, 'planejado', ?, ?, ?)""",
            (codigo, j["intencao_id"], j["cliente_id"], momento),
        )
        return resposta("check-in", "check_in_em", False, "Check-in realizado. Bom almoço!")

    if not j["visita_id"]:
        raise ErroAPI(409, "Esta visita ainda não fez check-in na entrada.")

    if modo == "balanca":
        if j["buffet_concluido_em"]:
            return resposta("buffet", "buffet_concluido_em", True, "Buffet já registrado.")
        banco.execute("UPDATE visita SET buffet_concluido_em = ? WHERE id = ?", (momento, j["visita_id"]))
        return resposta("buffet", "buffet_concluido_em", False, "Buffet concluído.")

    mesa = dados.get("mesa")
    if mesa in ("", None):
        mesa = None
    else:
        try:
            mesa = int(mesa)
            if not 1 <= mesa <= 999:
                raise ValueError
        except (TypeError, ValueError):
            raise ErroAPI(400, "Número de mesa inválido.")
    banco.execute(
        "UPDATE visita SET check_out_em = ?, saida_estimada = 0, mesa = COALESCE(?, mesa) WHERE id = ?",
        (momento, mesa, j["visita_id"]),
    )
    return resposta("check-out", "check_out_em", False, "Saída registrada. Obrigado pela visita!")


def avaliar(banco, codigo, dados):
    j = buscar_jornada(banco, codigo)
    if not j["check_out_em"]:
        raise ErroAPI(409, "A avaliação fica disponível depois da saída.")
    if j["nota_nps"] is not None:
        raise ErroAPI(409, "Esta visita já foi avaliada. Obrigado!")
    nps = dados.get("nota_nps")
    if type(nps) is not int or not 0 <= nps <= 10:
        raise ErroAPI(400, "Informe uma nota de 0 a 10.")
    temas = []
    for campo in ("nota_buffet", "nota_espera", "nota_atendimento"):
        nota = dados.get(campo)
        if type(nota) is not int or not 1 <= nota <= 5:
            raise ErroAPI(400, "Dê uma nota de 1 a 5 para Buffet, Espera e Atendimento.")
        temas.append(nota)
    comentario = dados.get("comentario", "")
    if not isinstance(comentario, str) or len(comentario.strip()) > 500:
        raise ErroAPI(400, "O comentário deve ter até 500 caracteres.")
    banco.execute(
        """INSERT INTO avaliacao (visita_id, nota_nps, nota_buffet, nota_espera, nota_atendimento,
                                  comentario, criada_em) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (j["visita_id"], nps, *temas, comentario.strip(), iso(agora())),
    )
    return 201, consultar(banco, codigo)


def consultar_cliente(banco, celular):
    celular = re.sub(r"\D", "", celular)
    linha = banco.execute("SELECT id FROM cliente WHERE celular = ?", (celular,)).fetchone()
    if linha is None:
        raise ErroAPI(404, "Cliente não encontrado.")
    return 200, {"visitas": visitas_do_cliente(banco, linha["id"])}


# ---------------------------------------------------------------- dashboard

def carregar_periodo(banco, inicio, fim):
    """Visitas (por check-in) e intenções (por horário previsto) entre os dias inicio e fim."""
    de, _ = limites_dia(inicio)
    _, ate = limites_dia(fim)
    visitas = [dict(l) for l in banco.execute(
        """SELECT v.*, a.nota_nps, a.nota_buffet, a.nota_espera, a.nota_atendimento, a.comentario,
                  a.criada_em AS avaliada_em, i.pessoas
           FROM visita v
           LEFT JOIN avaliacao a ON a.visita_id = v.id
           LEFT JOIN intencao i ON i.id = v.intencao_id
           WHERE v.check_in_em >= ? AND v.check_in_em < ? ORDER BY v.check_in_em""", (de, ate))]
    intencoes = [dict(l) for l in banco.execute(
        """SELECT i.*, v.id AS visita_id, v.check_in_em, v.check_out_em, a.visita_id AS avaliada
           FROM intencao i
           LEFT JOIN visita v ON v.intencao_id = i.id
           LEFT JOIN avaliacao a ON a.visita_id = v.id
           WHERE i.horario_previsto >= ? AND i.horario_previsto < ? ORDER BY i.horario_previsto""",
        (de, ate))]
    for v in visitas:
        v["dia"] = dia_local(v["check_in_em"])
        v["permanencia"] = (minutos(v["check_in_em"], v["check_out_em"])
                            if v["check_out_em"] and not v["saida_estimada"] else None)
        v["balanca"] = (minutos(v["check_in_em"], v["buffet_concluido_em"])
                        if v["buffet_concluido_em"] else None)
    for i in intencoes:
        i["dia"] = dia_local(i["horario_previsto"])
    return visitas, intencoes


def conversao(intencoes, referencia):
    elegiveis = [i for i in intencoes if ler_iso(i["horario_previsto"]) + TOLERANCIA_CHEGADA <= referencia]
    convertidas = sum(1 for i in elegiveis if i["visita_id"])
    return {"elegiveis": len(elegiveis), "convertidas": convertidas, "pct": pct(convertidas, len(elegiveis))}


def faixa_de(momento, tamanho=FAIXA):
    local = momento.astimezone(SP)
    base = local.replace(hour=0, minute=0, second=0, microsecond=0)
    passos = (local - base) // tamanho
    return base + passos * tamanho


def pratos_desejados(banco, dia):
    de, ate = limites_dia(dia)
    return [dict(l) for l in banco.execute(
        """SELECT p.id, p.nome, p.categoria, c.destaque,
                  (SELECT COUNT(*) FROM intencao_prato ip JOIN intencao i ON i.id = ip.intencao_id
                   WHERE ip.prato_id = p.id AND i.horario_previsto >= ? AND i.horario_previsto < ?) AS desejos
           FROM cardapio_dia c JOIN prato p ON p.id = c.prato_id
           WHERE c.data = ? ORDER BY desejos DESC, p.nome""", (de, ate, dia.isoformat()))]


def painel_hoje(banco, dia):
    momento = agora()
    hoje = hoje_local()
    fim_dia = inicio_dia(dia + timedelta(days=1))
    referencia = min(momento, fim_dia)
    visitas, intencoes = carregar_periodo(banco, dia, dia)

    planejados = [v for v in visitas if v["origem"] == "planejado"]
    espontaneos = [v for v in visitas if v["origem"] == "espontaneo"]
    avaliadas = [v for v in visitas if v["nota_nps"] is not None]

    # Série por 15 min: pessoas previstas × check-ins reais.
    eventos = [ler_iso(i["horario_previsto"]) for i in intencoes] + [ler_iso(v["check_in_em"]) for v in visitas]
    inicio_serie = inicio_dia(dia) + timedelta(hours=11)
    fim_serie = inicio_dia(dia) + timedelta(hours=15)
    if eventos:
        inicio_serie = min(inicio_serie, faixa_de(min(eventos), timedelta(hours=1)))
        fim_serie = max(fim_serie, faixa_de(max(eventos), timedelta(hours=1)) + timedelta(hours=1))
    faixas = {}
    passo = inicio_serie
    while passo < fim_serie:
        faixas[passo] = {"inicio": iso(passo), "previstas": 0, "planejados": 0, "espontaneos": 0}
        passo += FAIXA
    for i in intencoes:
        faixas[faixa_de(ler_iso(i["horario_previsto"]))]["previstas"] += i["pessoas"]
    for v in visitas:
        faixas[faixa_de(ler_iso(v["check_in_em"]))][v["origem"] + "s"] += 1

    # Próximas chegadas previstas (intenções ainda sem check-in), em janelas de 30 min.
    proximas = []
    if dia >= hoje:
        meia = timedelta(minutes=30)
        janela = faixa_de(max(momento, inicio_dia(dia)), meia)
        pendentes = [i for i in intencoes if not i["visita_id"]]
        while janela < fim_dia and len(proximas) < 4:
            grupo = [i for i in pendentes if janela <= ler_iso(i["horario_previsto"]) < janela + meia]
            if grupo:
                proximas.append({"inicio": iso(janela), "fim": iso(janela + meia),
                                 "pessoas": sum(i["pessoas"] for i in grupo), "intencoes": len(grupo)})
            janela += meia
    proxima_meia_hora = sum(
        i["pessoas"] for i in intencoes
        if not i["visita_id"] and momento <= ler_iso(i["horario_previsto"]) < momento + timedelta(minutes=30)
    )

    pratos = pratos_desejados(banco, dia)
    return {
        "data": dia.isoformat(),
        "atualizado_em": iso(momento),
        "ao_vivo": dia == hoje,
        "simulado": simulado(banco),
        "cartoes": {
            "visitas": len(visitas),
            "planejados": len(planejados),
            "espontaneos": len(espontaneos),
            "no_salao": (sum(1 for v in visitas if not v["check_out_em"]) if dia == hoje else None),
            "conversao": conversao(intencoes, referencia),
            "permanencia_media": media(v["permanencia"] for v in visitas if v["permanencia"] is not None),
            "balanca_media": media(v["balanca"] for v in visitas if v["balanca"] is not None),
            "nps": calcular_nps(v["nota_nps"] for v in avaliadas),
            "avaliacoes": len(avaliadas),
            "pessoas_previstas": sum(i["pessoas"] for i in intencoes),
        },
        "serie": list(faixas.values()),
        "proximas": proximas,
        "proxima_meia_hora": proxima_meia_hora,
        "pratos": pratos,
        "funil_planejados": [
            {"etapa": "Intenção", "valor": len(intencoes)},
            {"etapa": "Check-in", "valor": sum(1 for i in intencoes if i["visita_id"])},
            {"etapa": "Check-out", "valor": sum(1 for i in intencoes if i["check_out_em"])},
            {"etapa": "Avaliação", "valor": sum(1 for i in intencoes if i["avaliada"])},
        ],
        "espontaneos": {
            "visitas": len(espontaneos),
            "check_out": sum(1 for v in espontaneos if v["check_out_em"]),
            "avaliacoes": sum(1 for v in espontaneos if v["nota_nps"] is not None),
        },
    }


def painel_analise(banco, inicio, fim):
    if fim < inicio:
        raise ErroAPI(400, "A data final deve ser depois da inicial.")
    if (fim - inicio).days > 92:
        raise ErroAPI(400, "Escolha um período de até 92 dias.")
    momento = agora()
    visitas, intencoes = carregar_periodo(banco, inicio, fim)

    dias = []
    d = inicio
    while d <= fim:
        vd = [v for v in visitas if v["dia"] == d]
        idia = [i for i in intencoes if i["dia"] == d]
        dias.append({
            "data": d.isoformat(),
            "visitas": len(vd),
            "planejados": sum(1 for v in vd if v["origem"] == "planejado"),
            "espontaneos": sum(1 for v in vd if v["origem"] == "espontaneo"),
            "conversao": conversao(idia, min(momento, inicio_dia(d + timedelta(days=1))))["pct"],
            "permanencia_media": media(v["permanencia"] for v in vd if v["permanencia"] is not None),
            "nps": calcular_nps(v["nota_nps"] for v in vd if v["nota_nps"] is not None),
        })
        d += timedelta(days=1)

    # Pratos: desejos ÷ intenções dos dias em que o prato foi ofertado.
    intencoes_por_dia = Counter(i["dia"].isoformat() for i in intencoes)
    ofertas = banco.execute(
        """SELECT c.data, p.id, p.nome, p.categoria FROM cardapio_dia c JOIN prato p ON p.id = c.prato_id
           WHERE c.data BETWEEN ? AND ?""", (inicio.isoformat(), fim.isoformat())).fetchall()
    ids_intencao = [i["id"] for i in intencoes]
    desejos = Counter()
    if ids_intencao:
        marcas = ",".join("?" * len(ids_intencao))
        for l in banco.execute(f"SELECT prato_id FROM intencao_prato WHERE intencao_id IN ({marcas})", ids_intencao):
            desejos[l["prato_id"]] += 1
    resumo_pratos = {}
    for o in ofertas:
        r = resumo_pratos.setdefault(o["id"], {"nome": o["nome"], "categoria": o["categoria"],
                                               "dias": 0, "intencoes": 0, "desejos": desejos[o["id"]]})
        r["dias"] += 1
        r["intencoes"] += intencoes_por_dia.get(o["data"], 0)
    for r in resumo_pratos.values():
        r["taxa"] = pct(r["desejos"], r["intencoes"])
    com_base = [r for r in resumo_pratos.values() if r["intencoes"] >= 10]
    pouco_desejados = sorted(com_base, key=lambda r: (r["taxa"], -r["dias"]))[:6]
    mais_desejados = sorted(com_base, key=lambda r: -r["taxa"])[:3]

    avaliadas = [v for v in visitas if v["nota_nps"] is not None]
    notas = [v["nota_nps"] for v in avaliadas]
    satisfacao = {
        "nps": calcular_nps(notas),
        "avaliacoes": len(avaliadas),
        "promotores": sum(n >= 9 for n in notas),
        "neutros": sum(7 <= n <= 8 for n in notas),
        "detratores": sum(n <= 6 for n in notas),
        "temas": {tema: media(v[f"nota_{tema}"] for v in avaliadas) for tema in ("buffet", "espera", "atendimento")},
    }
    comentarios = [
        {"codigo": v["codigo"], "data": v["avaliada_em"], "nota_nps": v["nota_nps"], "comentario": v["comentario"]}
        for v in sorted(avaliadas, key=lambda v: v["avaliada_em"], reverse=True) if v["comentario"]
    ][:8]

    por_cliente = Counter(v["cliente_id"] for v in visitas if v["cliente_id"] and v["check_out_em"])
    faixas_rec = {"1": 0, "2": 0, "3": 0, "4+": 0}
    for qtd in por_cliente.values():
        faixas_rec["4+" if qtd >= 4 else str(qtd)] += 1
    recorrencia = {
        "clientes": len(por_cliente),
        "recorrentes": sum(1 for q in por_cliente.values() if q >= 2),
        "distribuicao": faixas_rec,
        "media_visitas": media(por_cliente.values()),
    }

    recentes = [{
        "codigo": v["codigo"], "origem": v["origem"], "check_in_em": v["check_in_em"],
        "check_out_em": v["check_out_em"], "saida_estimada": bool(v["saida_estimada"]),
        "permanencia": v["permanencia"], "nota_nps": v["nota_nps"],
    } for v in reversed(visitas[-30:])]

    total_conv = conversao(intencoes, momento)
    resumo = {
        "visitas": len(visitas),
        "planejados": sum(1 for v in visitas if v["origem"] == "planejado"),
        "conversao": total_conv,
        "permanencia_media": media(v["permanencia"] for v in visitas if v["permanencia"] is not None),
        "balanca_media": media(v["balanca"] for v in visitas if v["balanca"] is not None),
        "saidas_estimadas": sum(1 for v in visitas if v["saida_estimada"]),
    }
    return {
        "inicio": inicio.isoformat(), "fim": fim.isoformat(), "atualizado_em": iso(momento),
        "simulado": simulado(banco),
        "resumo": resumo, "dias": dias,
        "pratos_pouco_desejados": pouco_desejados,
        "satisfacao": satisfacao, "comentarios": comentarios,
        "recorrencia": recorrencia, "recentes": recentes,
        "insights": gerar_insights(visitas, intencoes, dias, resumo, satisfacao, mais_desejados,
                                   pouco_desejados, recorrencia),
    }


def gerar_insights(visitas, intencoes, dias, resumo, satisfacao, mais, menos, recorrencia):
    """Frases geradas por regras sobre os dados do período. Nada de texto fixo."""
    frases = []
    dias_com_visita = [d for d in dias if d["visitas"]]
    if not visitas:
        return ["Ainda não há visitas registradas neste período."]

    picos = Counter(faixa_de(ler_iso(v["check_in_em"])).strftime("%H:%M") for v in visitas)
    hora, qtd = max(picos.items(), key=lambda par: (par[1], par[0]))
    fim_pico = (datetime.strptime(hora, "%H:%M") + FAIXA).strftime("%H:%M")
    frases.append(f"Maior pico de chegadas entre {hora.replace(':', 'h')} e {fim_pico.replace(':', 'h')}: "
                  f"média de {br(qtd / max(len(dias_com_visita), 1))} chegadas por dia nesses 15 minutos.")

    melhor_dia = max(dias_com_visita, key=lambda d: d["visitas"])
    nome_dia = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"][
        date.fromisoformat(melhor_dia["data"]).weekday()]
    frases.append(f"Dia mais movimentado: {nome_dia}, {date.fromisoformat(melhor_dia['data']).strftime('%d/%m')}, "
                  f"com {melhor_dia['visitas']} visitas.")

    frases.append(f"Planejados foram {pct(resumo['planejados'], resumo['visitas'])}% das visitas "
                  f"({resumo['planejados']} de {resumo['visitas']}).")

    conv = resumo["conversao"]
    if conv["elegiveis"]:
        faltas = conv["elegiveis"] - conv["convertidas"]
        frases.append(f"{conv['pct']}% das intenções viraram visita; {faltas} "
                      f"{'intenção ficou' if faltas == 1 else 'intenções ficaram'} sem comparecimento.")

    if mais:
        frases.append(f"Prato mais desejado: {mais[0]['nome']}, marcado em {mais[0]['taxa']}% das intenções "
                      f"dos dias em que foi servido.")
    if menos and mais and menos[0]["nome"] != mais[0]["nome"]:
        frases.append(f"Menor interesse: {menos[0]['nome']} ({menos[0]['taxa']}% das intenções em "
                      f"{menos[0]['dias']} dia{'s' if menos[0]['dias'] > 1 else ''} de oferta). "
                      f"Avaliar reposição ou troca.")

    temas = {k: v for k, v in satisfacao["temas"].items() if v is not None}
    if temas:
        pior = min(temas, key=temas.get)
        nomes = {"buffet": "Buffet", "espera": "Espera", "atendimento": "Atendimento"}
        frases.append(f"{nomes[pior]} tem a menor nota média ({br(temas[pior])} de 5) "
                      f"entre {satisfacao['avaliacoes']} avaliações.")

    if recorrencia["clientes"]:
        frases.append(f"{recorrencia['recorrentes']} de {recorrencia['clientes']} clientes identificados "
                      f"voltaram mais de uma vez no período.")

    if resumo["saidas_estimadas"]:
        frases.append(f"{resumo['saidas_estimadas']} visitas ficaram sem check-out e foram fechadas "
                      f"automaticamente após 3 h. Reforçar o registro no caixa.")
    return frases


def exportar_csv(banco, inicio, fim):
    visitas, _ = carregar_periodo(banco, inicio, fim)
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["codigo", "origem", "data", "chegada", "buffet", "saida", "saida_estimada",
                       "permanencia_min", "mesa", "pessoas", "nps", "nota_buffet", "nota_espera",
                       "nota_atendimento", "comentario"])

    def hora(texto):
        return ler_iso(texto).astimezone(SP).strftime("%H:%M") if texto else ""

    for v in visitas:
        escritor.writerow([
            v["codigo"], v["origem"], v["dia"].strftime("%d/%m/%Y"), hora(v["check_in_em"]),
            hora(v["buffet_concluido_em"]), hora(v["check_out_em"]), "sim" if v["saida_estimada"] else "não",
            "" if v["permanencia"] is None else round(v["permanencia"]), v["mesa"] or "", v["pessoas"] or "",
            "" if v["nota_nps"] is None else v["nota_nps"], v["nota_buffet"] or "", v["nota_espera"] or "",
            v["nota_atendimento"] or "", v["comentario"] or "",
        ])
    return "﻿" + saida.getvalue()


# ---------------------------------------------------------------- HTTP

class Servidor(BaseHTTPRequestHandler):
    server_version = "BovinusConnect/2"

    def log_message(self, formato, *args):
        if not self.path.startswith(("/api/dashboard", "/api/jornadas/BOV")) or "GET" not in self.requestline:
            super().log_message(formato, *args)

    def enviar(self, status, corpo, tipo, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        for chave, valor in (extra or {}).items():
            self.send_header(chave, valor)
        self.end_headers()
        self.wfile.write(corpo)

    def responder(self, status, dados, extra=None):
        self.enviar(status, json.dumps(dados, ensure_ascii=False).encode(), "application/json; charset=utf-8", extra)

    def token(self):
        try:
            biscoito = SimpleCookie(self.headers.get("Cookie", ""))
        except CookieError:
            return None
        return biscoito[COOKIE].value if COOKIE in biscoito else None

    def cookie_sessao(self, token, duracao):
        return {"Set-Cookie": f"{COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={duracao}"}

    def ler_json(self):
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if tamanho == 0:
                return {}
            if not 0 < tamanho <= 16384:
                raise ValueError
            dados = json.loads(self.rfile.read(tamanho))
            if not isinstance(dados, dict):
                raise ValueError
            return dados
        except (ValueError, RecursionError):
            raise ErroAPI(400, "Envie um objeto JSON válido.")

    def do_GET(self):
        self.atender()

    def do_POST(self):
        self.atender()

    def do_PUT(self):
        self.atender()

    def do_DELETE(self):
        self.atender()

    def arquivo_estatico(self, caminho):
        nome = caminho.lstrip("/")
        if caminho in PAGINAS:
            nome = PAGINAS[caminho]
        elif caminho.endswith(".html") and nome in PAGINAS.values():
            pass
        elif nome in ARQUIVOS:
            pass
        elif nome.split("/", 1)[0] in PASTAS_ESTATICAS:
            alvo = (PASTA / nome).resolve()
            if not alvo.is_file() or not alvo.is_relative_to(PASTA / nome.split("/", 1)[0]):
                return None
        else:
            return None
        alvo = PASTA / nome
        if not alvo.is_file():
            return None
        tipo = mimetypes.guess_type(alvo.name)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo.endswith("javascript"):
            tipo += "; charset=utf-8"
        return alvo.read_bytes(), tipo, nome

    def atender(self):
        url = urlsplit(self.path)
        caminho = url.path
        consulta = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if self.command == "GET" and not caminho.startswith("/api/"):
                arquivo = self.arquivo_estatico(caminho)
                if arquivo is None:
                    return self.enviar(404, "Página não encontrada.".encode(), "text/plain; charset=utf-8")
                papeis = PAGINAS_EQUIPE.get(arquivo[2])
                if papeis:
                    with closing(conectar()) as banco:
                        usuario = usuario_da_sessao(banco, self.token())
                    if not usuario or usuario["papel"] not in papeis:
                        destino = "/login?volta=" + quote(self.path, safe="") + ("&negado=1" if usuario else "")
                        return self.enviar(302, b"", "text/plain", {"Location": destino})
                return self.enviar(200, *arquivo[:2])
            partes = caminho.strip("/").split("/")[1:]  # remove "api"
            with closing(conectar()) as banco, banco:
                self.usuario = usuario_da_sessao(banco, self.token())
                papeis = papeis_exigidos(self.command, partes)
                if papeis and not self.usuario:
                    raise ErroAPI(401, "Faça login para continuar.")
                if papeis and self.usuario["papel"] not in papeis:
                    raise ErroAPI(403, "Seu usuário não tem acesso a esta função.")
                if self.command == "GET":
                    fechar_visitas_antigas(banco)
                    resultado = self.rota_get(banco, caminho, consulta)
                else:
                    dados = self.ler_json()
                    if self.headers.get("Content-Length", "0") != "0" and \
                            not self.headers.get("Content-Type", "").startswith("application/json"):
                        raise ErroAPI(415, "Envie o corpo como application/json.")
                    banco.execute("BEGIN IMMEDIATE")
                    fechar_visitas_antigas(banco)
                    resultado = self.rota_escrita(banco, caminho, dados)
            if isinstance(resultado, bytes):
                nome = f"visitas_{consulta.get('inicio', '')}_{consulta.get('fim', '')}.csv"
                return self.enviar(200, resultado, "text/csv; charset=utf-8",
                                   {"Content-Disposition": f'attachment; filename="{nome}"'})
            self.responder(*resultado)
        except ErroAPI as erro:
            self.responder(erro.status, {"erro": str(erro)})
        except sqlite3.IntegrityError as erro:
            self.log_error("%s", erro)
            self.responder(409, {"erro": "Os dados não puderam ser gravados (conflito)."})
        except sqlite3.OperationalError as erro:
            self.log_error("%s", erro)
            self.responder(503, {"erro": "Banco temporariamente indisponível."})

    def rota_get(self, banco, caminho, consulta):
        partes = caminho.strip("/").split("/")[1:]  # remove "api"
        if partes == ["eu"]:
            if not self.usuario:
                raise ErroAPI(401, "Faça login para continuar.")
            return 200, self.usuario
        if partes == ["cardapio"]:
            return 200, listar_cardapio(banco, ler_data(consulta.get("data")))
        if len(partes) == 2 and partes[0] == "jornadas":
            return 200, consultar(banco, normalizar_codigo(partes[1]))
        if len(partes) == 2 and partes[0] == "clientes":
            return consultar_cliente(banco, partes[1])
        if partes == ["dashboard", "hoje"]:
            return 200, painel_hoje(banco, ler_data(consulta.get("data")))
        if partes in (["dashboard", "analise"], ["visitas.csv"]):
            fim = ler_data(consulta.get("fim"))
            inicio = ler_data(consulta.get("inicio"), fim - timedelta(days=6))
            if partes[0] == "visitas.csv":
                return exportar_csv(banco, inicio, fim).encode("utf-8")
            return 200, painel_analise(banco, inicio, fim)
        raise ErroAPI(404, "Rota não encontrada.")

    def rota_escrita(self, banco, caminho, dados):
        partes = caminho.strip("/").split("/")[1:]
        metodo = self.command
        if metodo == "POST" and partes == ["login"]:
            token, usuario = entrar(banco, dados, self.client_address[0])
            return 200, usuario, self.cookie_sessao(token, int(DURACAO_SESSAO.total_seconds()))
        if metodo == "POST" and partes == ["logout"]:
            if self.token():
                banco.execute("DELETE FROM sessao WHERE token_hash = ?", (hash_token(self.token()),))
            return 200, {"ok": True}, self.cookie_sessao("", 0)
        if metodo == "POST" and partes == ["intencoes"]:
            return criar_intencao(banco, dados)
        if metodo == "POST" and partes == ["visitas"]:
            return criar_visita_espontanea(banco)
        if metodo == "POST" and len(partes) == 3 and partes[0] == "jornadas":
            codigo = normalizar_codigo(partes[1])
            if partes[2] == "proxima":
                return registrar_proxima(banco, codigo, dados)
            if partes[2] == "avaliacao":
                return avaliar(banco, codigo, dados)
        if partes and partes[0] == "cardapio" and len(partes) >= 2:
            dia = ler_data(partes[1])
            if metodo == "POST" and len(partes) == 2:
                return adicionar_prato(banco, dia, dados)
            if metodo == "POST" and partes[2:] == ["copiar-anterior"]:
                return copiar_cardapio_anterior(banco, dia)
            if len(partes) == 3 and partes[2].isdigit():
                if metodo == "PUT":
                    return editar_prato(banco, dia, int(partes[2]), dados)
                if metodo == "DELETE":
                    return remover_prato(banco, dia, int(partes[2]))
        raise ErroAPI(404, "Rota não encontrada.")


def endereco_rede():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))  # não envia pacotes; só descobre a interface local
            return s.getsockname()[0]
    except OSError:
        return None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    preparar_banco()
    host = os.environ.get("BOVINUS_HOST", "0.0.0.0")
    porta = int(os.environ.get("BOVINUS_PORTA", "8000"))
    with ThreadingHTTPServer((host, porta), Servidor) as servidor:
        print("Bovinu's Connect no ar:", flush=True)
        print(f"  Neste computador:  http://127.0.0.1:{porta}", flush=True)
        ip = endereco_rede()
        if host == "0.0.0.0" and ip:
            print(f"  No celular (mesma rede Wi-Fi):  http://{ip}:{porta}", flush=True)
        print("  Cliente: /  e  /avaliar   ·   Equipe (com login): /terminal  /cardapio  /dashboard", flush=True)
        print("Ctrl+C para encerrar.", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass
