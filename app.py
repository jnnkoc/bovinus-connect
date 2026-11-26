import json
import os
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PASTA = Path(__file__).resolve().parent
BANCO = Path(os.environ.get("BOVINUS_BANCO", PASTA / "bovinus.db"))
CODIGO = re.compile(r"[0-9A-F]{12}")
ETAPAS = {
    "check-in": "check_in_em",
    "buffet": "buffet_concluido_em",
    "check-out": "check_out_em",
}


class ErroAPI(Exception):
    def __init__(self, status, mensagem):
        self.status = status
        super().__init__(mensagem)


def conectar():
    banco = sqlite3.connect(BANCO, timeout=10)
    banco.row_factory = sqlite3.Row
    banco.execute("PRAGMA foreign_keys = ON")
    return banco


def utc(data=None):
    return (data or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(
        timespec="milliseconds"
    )


def criar_intencao(banco, dados):
    try:
        previsto = datetime.fromisoformat(dados["horario_previsto"].replace("Z", "+00:00"))
        if previsto.utcoffset() is None:
            raise ValueError
        previsto = utc(previsto)
    except (KeyError, AttributeError, ValueError, OverflowError):
        raise ErroAPI(400, "Informe horario_previsto em formato ISO com fuso horário.")

    for _ in range(5):
        codigo = secrets.token_hex(6).upper()
        insercao = banco.execute(
            """INSERT INTO intencao (codigo, horario_previsto, criada_em)
               VALUES (?, ?, ?) ON CONFLICT(codigo) DO NOTHING""",
            (codigo, previsto, utc()),
        )
        if insercao.rowcount:
            return 201, consultar(banco, codigo)
    raise ErroAPI(503, "Tente gerar o código novamente.")


def consultar(banco, codigo):
    linha = banco.execute("SELECT * FROM jornada WHERE codigo_visita = ?", (codigo,)).fetchone()
    if linha is None:
        raise ErroAPI(404, "Código de visita não encontrado.")
    return dict(linha)


def registrar_etapa(banco, codigo, etapa):
    jornada = consultar(banco, codigo)
    campo = ETAPAS[etapa]
    if jornada[campo] is not None:
        return jornada

    agora = utc()
    if etapa == "check-in":
        banco.execute(
            "INSERT INTO visita (id, check_in_em) SELECT id, ? FROM intencao WHERE codigo = ?",
            (agora, codigo),
        )
    else:
        anterior = "check_in_em" if etapa == "buffet" else "buffet_concluido_em"
        if jornada[anterior] is None:
            raise ErroAPI(409, "Registre a etapa anterior primeiro.")
        banco.execute(
            f"UPDATE visita SET {campo} = ? WHERE id = (SELECT id FROM intencao WHERE codigo = ?)",
            (max(agora, jornada[anterior]), codigo),
        )
    return consultar(banco, codigo)


def avaliar(banco, codigo, dados):
    jornada = consultar(banco, codigo)
    if jornada["check_out_em"] is None:
        raise ErroAPI(409, "A avaliação fica disponível depois do check-out.")
    nota = dados.get("nota_nps")
    comentario = dados.get("comentario", "")
    if type(nota) is not int or not 0 <= nota <= 10:
        raise ErroAPI(400, "Informe uma nota inteira de 0 a 10.")
    if not isinstance(comentario, str) or len(comentario) > 500:
        raise ErroAPI(400, "O comentário deve ter até 500 caracteres.")
    if jornada["nota_nps"] is not None:
        if (nota, comentario) == (jornada["nota_nps"], jornada["comentario"]):
            return jornada
        raise ErroAPI(409, "Esta visita já tem uma avaliação.")
    banco.execute(
        """INSERT INTO avaliacao (visita_id, nota_nps, comentario)
           SELECT id, ?, ? FROM intencao WHERE codigo = ?""",
        (nota, comentario, codigo),
    )
    return consultar(banco, codigo)


class Servidor(BaseHTTPRequestHandler):
    def enviar(self, status, corpo, tipo):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def responder(self, status, dados):
        self.enviar(status, json.dumps(dados, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def ler_json(self):
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= 8192:
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

    def atender(self):
        try:
            if self.command == "GET" and self.path in ("/", "/terminal"):
                return self.enviar(200, (PASTA / "terminal.html").read_bytes(), "text/html; charset=utf-8")
            with closing(conectar()) as banco, banco:
                if self.command == "POST":
                    dados = self.ler_json()
                    banco.execute("BEGIN IMMEDIATE")
                    status, resultado = self.rota_post(banco, dados)
                else:
                    status, resultado = self.rota_get(banco)
            self.responder(status, resultado)
        except ErroAPI as erro:
            self.responder(erro.status, {"erro": str(erro)})
        except sqlite3.OperationalError as erro:
            self.log_error("%s", erro)
            self.responder(503, {"erro": "Banco temporariamente indisponível."})

    def rota_get(self, banco):
        if self.path == "/api/jornadas":
            linhas = banco.execute("SELECT * FROM jornada ORDER BY horario_previsto, codigo_visita")
            return 200, [dict(linha) for linha in linhas]
        caminho = self.path.split("/")
        if len(caminho) == 4 and caminho[:3] == ["", "api", "jornadas"]:
            return 200, consultar(banco, caminho[3].upper())
        raise ErroAPI(404, "Rota não encontrada.")

    def rota_post(self, banco, dados):
        if self.path == "/api/intencoes":
            return criar_intencao(banco, dados)
        caminho = self.path.split("/")
        if len(caminho) == 5 and caminho[:3] == ["", "api", "jornadas"]:
            codigo, acao = caminho[3].upper(), caminho[4]
            if not CODIGO.fullmatch(codigo):
                raise ErroAPI(400, "Formato de código inválido.")
            if acao in ETAPAS:
                return 200, registrar_etapa(banco, codigo, acao)
            if acao == "avaliacao":
                return 200, avaliar(banco, codigo, dados)
        raise ErroAPI(404, "Rota não encontrada.")


if __name__ == "__main__":
    with closing(conectar()) as banco:
        banco.executescript((PASTA / "schema.sql").read_text(encoding="utf-8"))
    porta = int(os.environ.get("BOVINUS_PORTA", "8000"))
    with ThreadingHTTPServer(("127.0.0.1", porta), Servidor) as servidor:
        print(f"Terminal disponível em http://127.0.0.1:{porta}", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass
