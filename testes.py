"""Testes automatizados do Bovinu's Connect (só biblioteca padrão).

Rodar:  py testes.py      (Linux/macOS: python3 testes.py)
Sobe o servidor numa porta livre com um banco TEMPORÁRIO: não mexe no bovinus.db.
"""
import json
import tempfile
import threading
import unittest
import urllib.error
from unittest import mock
import urllib.request
from contextlib import closing
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

import app

SENHA_GERENTE = "senha-gerente-1"
SENHA_ATENDENTE = "senha-atendente-1"


class SemRedirecionar(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


abrir = urllib.request.build_opener(SemRedirecionar).open


class TesteBovinus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = tempfile.TemporaryDirectory()
        app.BANCO = Path(cls.pasta.name) / "teste.db"
        app.preparar_banco(criar_usuarios=False)
        with closing(app.conectar()) as banco, banco:
            app.criar_usuario(banco, "gerente", "Gerente Teste", "gerente", SENHA_GERENTE)
            app.criar_usuario(banco, "atendente", "Atendente Teste", "atendente", SENHA_ATENDENTE)
        cls.servidor = ThreadingHTTPServer(("127.0.0.1", 0), app.Servidor)
        cls.servidor.RequestHandlerClass.log_message = lambda *a: None  # silencia o log nos testes
        cls.base = f"http://127.0.0.1:{cls.servidor.server_address[1]}"
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()
        cls.gerente = cls.entrar("gerente", SENHA_GERENTE)
        cls.atendente = cls.entrar("atendente", SENHA_ATENDENTE)
        # horário previsto de hoje (10 min atrás: ainda dentro da tolerância de 30 min, então "a chegar")
        cls.previsto = (app.agora() - timedelta(minutes=10)).astimezone(app.SP)
        cls.dia = cls.previsto.date().isoformat()
        cls.pratos = []
        for nome, cat in (("Picanha", "churrasco"), ("Arroz", "acompanhamento"), ("Salada verde", "salada"), ("Pudim", "sobremesa")):
            _, r = cls.chamar("POST", f"/api/cardapio/{cls.dia}", {"nome": nome, "categoria": cat}, cls.gerente)
        cls.pratos = [p["id"] for p in r["pratos"]]

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.pasta.cleanup()

    @classmethod
    def chamar(cls, metodo, rota, dados=None, cookie=None):
        corpo = None if dados is None else json.dumps(dados).encode()
        req = urllib.request.Request(cls.base + rota, data=corpo, method=metodo)
        if corpo is not None:
            req.add_header("Content-Type", "application/json")
        if cookie:
            req.add_header("Cookie", cookie)
        try:
            with abrir(req) as r:
                bruto = r.read()
                return r.status, (json.loads(bruto) if "json" in r.headers.get("Content-Type", "") else bruto)
        except urllib.error.HTTPError as e:
            bruto = e.read()
            try:
                return e.code, json.loads(bruto)
            except ValueError:
                return e.code, e.headers

    @classmethod
    def entrar(cls, login, senha):
        req = urllib.request.Request(cls.base + "/api/login", method="POST",
                                     data=json.dumps({"login": login, "senha": senha}).encode(),
                                     headers={"Content-Type": "application/json"})
        with abrir(req) as r:
            return r.headers["Set-Cookie"].split(";")[0]

    def nova_intencao(self, pratos=None, celular="11988887777"):
        return self.chamar("POST", "/api/intencoes", {
            "horario_previsto": self.previsto.isoformat(), "pessoas": 2,
            "pratos": self.pratos[:3] if pratos is None else pratos,
            "nome": "Cliente Teste", "celular": celular, "aceite_lgpd": True})

    # ------------------------------------------------------------ login e permissões
    def test_paginas_da_equipe_pedem_login(self):
        for pagina in ("/terminal", "/cardapio", "/dashboard", "/dashboard.html"):
            status, cabecalhos = self.chamar("GET", pagina)
            self.assertEqual(status, 302, pagina)
            self.assertTrue(cabecalhos["Location"].startswith("/login?volta="), pagina)

    def test_paginas_do_cliente_sao_publicas(self):
        for pagina in ("/", "/avaliar", "/login", "/estilo.css", "/vendor/qrcode.js", "/img/logo.png"):
            self.assertEqual(self.chamar("GET", pagina)[0], 200, pagina)

    def test_papeis(self):
        self.assertEqual(self.chamar("GET", "/dashboard", cookie=self.gerente)[0], 200)
        self.assertEqual(self.chamar("GET", "/terminal", cookie=self.atendente)[0], 200)
        status, cab = self.chamar("GET", "/dashboard", cookie=self.atendente)
        self.assertEqual(status, 302)
        self.assertIn("negado=1", cab["Location"])
        self.assertEqual(self.chamar("GET", "/api/dashboard/hoje", cookie=self.atendente)[0], 403)
        self.assertEqual(self.chamar("POST", f"/api/cardapio/{self.dia}", {"nome": "X Y", "categoria": "salada"}, self.atendente)[0], 403)

    def test_api_da_equipe_exige_login(self):
        self.assertEqual(self.chamar("GET", "/api/dashboard/hoje")[0], 401)
        self.assertEqual(self.chamar("GET", "/api/visitas.csv")[0], 401)
        self.assertEqual(self.chamar("POST", "/api/visitas", {})[0], 401)
        self.assertEqual(self.chamar("POST", "/api/jornadas/BOV-ABCD/proxima", {"modo": "entrada"})[0], 401)
        self.assertEqual(self.chamar("POST", f"/api/cardapio/{self.dia}", {"nome": "X Y", "categoria": "salada"})[0], 401)
        self.assertEqual(self.chamar("GET", "/api/clientes/11988887777")[0], 401)

    def test_senha_errada_e_bloqueio(self):
        for _ in range(app.MAX_FALHAS_LOGIN):
            self.assertEqual(self.chamar("POST", "/api/login", {"login": "ninguem", "senha": "errada123"})[0], 401)
        self.assertEqual(self.chamar("POST", "/api/login", {"login": "ninguem", "senha": "errada123"})[0], 429)

    def test_logout_encerra_sessao(self):
        cookie = self.entrar("gerente", SENHA_GERENTE)
        self.assertEqual(self.chamar("GET", "/api/eu", cookie=cookie)[1]["papel"], "gerente")
        self.chamar("POST", "/api/logout", {}, cookie)
        self.assertEqual(self.chamar("GET", "/api/eu", cookie=cookie)[0], 401)

    def test_senha_guardada_com_hash(self):
        with closing(app.conectar()) as banco:
            guardada = banco.execute("SELECT senha_hash FROM usuario WHERE login='gerente'").fetchone()[0]
        self.assertNotIn(SENHA_GERENTE, guardada)
        self.assertTrue(app.conferir_senha(SENHA_GERENTE, guardada))
        self.assertFalse(app.conferir_senha("outra", guardada))

    def test_caminho_fora_da_pasta_bloqueado(self):
        for caminho in ("/app.py", "/img/../app.py", "/vendor/../bovinus.db", "/schema.sql"):
            self.assertEqual(self.chamar("GET", caminho)[0], 404, caminho)

    # ------------------------------------------------------------ jornada
    def test_fluxo_planejado_completo(self):
        status, v = self.nova_intencao(celular="11911112222")
        self.assertEqual(status, 201)
        self.assertRegex(v["codigo"], r"^BOV-[2-9A-HJ-NP-Z]{4}$")
        codigo = v["codigo"]
        self.assertEqual(self.chamar("GET", f"/api/jornadas/{codigo[4:].lower()}")[1]["status"], "aguardando")
        self.assertEqual(self.chamar("POST", f"/api/jornadas/{codigo}/proxima", {"modo": "caixa"}, self.atendente)[0], 409)
        s, r = self.chamar("POST", f"/api/jornadas/{codigo}/proxima", {"modo": "entrada"}, self.atendente)
        self.assertEqual((s, r["etapa"], r["repetido"]), (200, "check-in", False))
        self.assertTrue(self.chamar("POST", f"/api/jornadas/{codigo}/proxima", {"modo": "entrada"}, self.atendente)[1]["repetido"])
        self.assertEqual(self.chamar("POST", f"/api/jornadas/{codigo}/avaliacao", {"nota_nps": 9, "nota_buffet": 5, "nota_espera": 4, "nota_atendimento": 5})[0], 409)
        s, r = self.chamar("POST", f"/api/jornadas/{codigo}/proxima", {"modo": "caixa", "mesa": "15"}, self.atendente)
        self.assertEqual((r["visita"]["status"], r["visita"]["mesa"]), ("encerrada", 15))  # buffet é opcional
        s, r = self.chamar("POST", f"/api/jornadas/{codigo}/avaliacao", {
            "nota_nps": 9, "nota_buffet": 5, "nota_espera": 4, "nota_atendimento": 5, "comentario": "Ótimo, voltarei!"})
        self.assertEqual(s, 201)
        self.assertTrue(r["avaliada"])
        self.assertEqual(r["visitas_cliente"], 1)
        self.assertEqual(self.chamar("POST", f"/api/jornadas/{codigo}/avaliacao", {"nota_nps": 1, "nota_buffet": 1, "nota_espera": 1, "nota_atendimento": 1})[0], 409)
        self.assertNotIn("celular", json.dumps(r))  # consulta pública sem dados pessoais

    def test_espontaneo(self):
        s, v = self.chamar("POST", "/api/visitas", {}, self.atendente)
        self.assertEqual((s, v["origem"], v["status"]), (201, "espontaneo", "em_andamento"))
        self.assertEqual(self.chamar("POST", f"/api/jornadas/{v['codigo']}/proxima", {"modo": "balanca"}, self.atendente)[1]["etapa"], "buffet")
        self.assertEqual(self.chamar("POST", f"/api/jornadas/{v['codigo']}/proxima", {"modo": "caixa"}, self.atendente)[1]["visita"]["status"], "encerrada")

    def test_regras_da_intencao(self):
        self.assertEqual(self.nova_intencao(pratos=self.pratos[:4])[0], 400)  # máximo 3 pratos
        self.assertEqual(self.nova_intencao(pratos=[99999])[0], 400)          # prato fora do cardápio
        s, r = self.chamar("POST", "/api/intencoes", {"horario_previsto": self.previsto.isoformat(), "nome": "A B", "celular": "11988887777"})
        self.assertEqual(s, 400)  # sem aceite LGPD
        passado = (app.agora() - timedelta(hours=2)).isoformat()
        self.assertEqual(self.chamar("POST", "/api/intencoes", {"horario_previsto": passado, "nome": "A B", "celular": "11988887777", "aceite_lgpd": True})[0], 400)

    def test_entrada_com_intencao_de_outro_dia(self):
        amanha = (app.agora() + timedelta(days=1)).astimezone(app.SP).replace(hour=12, minute=30)
        s, v = self.chamar("POST", "/api/intencoes", {"horario_previsto": amanha.isoformat(), "pratos": [],
                                                      "nome": "Cliente Amanhã", "celular": "11955556666", "aceite_lgpd": True})
        self.assertEqual(s, 201)
        s, r = self.chamar("POST", f"/api/jornadas/{v['codigo']}/proxima", {"modo": "entrada"}, self.atendente)
        self.assertEqual(s, 409)
        self.assertTrue(r["outro_dia"])
        self.assertEqual(r["erro"], f"Esta visita está marcada para {amanha.strftime('%d/%m')}.")
        self.assertEqual(self.chamar("GET", f"/api/jornadas/{v['codigo']}")[1]["status"], "aguardando")  # nada registrado
        self.assertEqual(self.chamar("POST", "/api/visitas", {}, self.atendente)[0], 201)  # "Registrar como espontâneo"

    def test_agora_de_demonstracao(self):
        hoje = app.agora().astimezone(app.SP).date()
        noite = datetime.combine(hoje, datetime.min.time(), app.SP).replace(hour=21)
        almoco = noite.replace(hour=13, minute=5)
        with closing(app.conectar()) as banco:
            try:
                with mock.patch.object(app, "agora", return_value=noite):
                    self.assertEqual(app.agora_referencia(banco), (noite, False))  # banco sem dados simulados
                    banco.execute("INSERT INTO parametro VALUES ('dados_simulados', '1')")
                    self.assertEqual(app.agora_referencia(banco), (noite.replace(hour=12, minute=40), True))
                    with mock.patch.dict(app.os.environ, {"DEMO_AGORA": "13:15"}):
                        self.assertEqual(app.agora_referencia(banco)[0], noite.replace(hour=13, minute=15))
                    with mock.patch.dict(app.os.environ, {"DEMO_AGORA": "off"}):
                        self.assertEqual(app.agora_referencia(banco), (noite, False))
                with mock.patch.object(app, "agora", return_value=almoco):
                    self.assertEqual(app.agora_referencia(banco), (almoco, False))  # no almoço vale o real
            finally:
                banco.rollback()
        with self.assertRaises(ValueError):
            app.ler_hora_demo("25h")

    def test_codigos(self):
        self.assertEqual(self.chamar("GET", "/api/jornadas/BOV-0O1I")[0], 400)
        self.assertEqual(self.chamar("GET", "/api/jornadas/BOV-ZZZZ")[0], 404)

    def test_visita_aberta_fecha_sozinha_apos_3h(self):
        with closing(app.conectar()) as banco, banco:
            antigo = app.iso(app.agora() - timedelta(hours=4))
            banco.execute("INSERT INTO visita (codigo, origem, check_in_em) VALUES ('BOV-TTTT', 'espontaneo', ?)", (antigo,))
        v = self.chamar("GET", "/api/jornadas/BOV-TTTT")[1]
        self.assertEqual((v["status"], v["saida_estimada"]), ("encerrada", True))

    # ------------------------------------------------------------ cardápio e dashboard
    def test_cardapio_crud(self):
        dia = (datetime.fromisoformat(self.dia) + timedelta(days=3)).date().isoformat()
        s, r = self.chamar("POST", f"/api/cardapio/{dia}/copiar-anterior", {}, self.gerente)
        self.assertEqual((s, len(r["pratos"])), (200, 4))
        s, r = self.chamar("POST", f"/api/cardapio/{dia}", {"nome": "Polenta", "categoria": "acompanhamento", "vegetariano": True}, self.gerente)
        pid = next(p["id"] for p in r["pratos"] if p["nome"] == "Polenta")
        s, r = self.chamar("PUT", f"/api/cardapio/{dia}/{pid}", {"nome": "Polenta frita", "categoria": "acompanhamento", "destaque": True}, self.gerente)
        self.assertTrue(any(p["nome"] == "Polenta frita" and p["destaque"] for p in r["pratos"]))
        self.assertEqual(self.chamar("DELETE", f"/api/cardapio/{dia}/{pid}", cookie=self.gerente)[0], 200)
        self.assertEqual(len(self.chamar("GET", f"/api/cardapio?data={dia}")[1]["pratos"]), 4)

    def test_dashboard(self):
        self.nova_intencao(celular="11933334444")
        s, h = self.chamar("GET", f"/api/dashboard/hoje?data={self.dia}", cookie=self.gerente)
        self.assertEqual(s, 200)
        self.assertGreaterEqual(h["funil_planejados"][0]["valor"], 1)
        self.assertTrue(any(p["desejos"] for p in h["pratos"]))
        si = h["intencoes_situacao"]
        self.assertEqual(si["chegaram"] + si["a_chegar"] + si["nao_compareceram"], si["total"])
        self.assertEqual(si["total"], h["funil_planejados"][0]["valor"])
        self.assertGreaterEqual(si["a_chegar"], 1)  # previsto há 10 min, sem check-in: ainda por chegar
        s, a = self.chamar("GET", "/api/dashboard/analise", cookie=self.gerente)
        self.assertEqual(s, 200)
        self.assertTrue(a["insights"])
        s, csv = self.chamar("GET", "/api/visitas.csv", cookie=self.gerente)
        self.assertEqual(s, 200)
        self.assertTrue(csv.decode("utf-8-sig").startswith("codigo;origem"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
