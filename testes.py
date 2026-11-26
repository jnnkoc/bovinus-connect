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
        # (logo depois da meia-noite, usa 00:01 de hoje, para a intenção não cair em "outro dia")
        cls.previsto = max((app.agora() - timedelta(minutes=10)).astimezone(app.SP),
                           app.inicio_dia(app.hoje_local()) + timedelta(minutes=1))
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
        for pagina in ("/", "/minha-visita", "/avaliar", "/login", "/estilo.css", "/vendor/qrcode.js", "/img/logo.png"):
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

    # ------------------------------------------------------------ fidelidade e cadastro
    def visita_completa(self, codigo, mesa=None, avaliar=True):
        self.chamar("POST", f"/api/jornadas/{codigo}/proxima", {"modo": "entrada"}, self.atendente)
        self.chamar("POST", f"/api/jornadas/{codigo}/proxima", {"modo": "caixa", "mesa": mesa}, self.atendente)
        if avaliar:
            s, r = self.chamar("POST", f"/api/jornadas/{codigo}/avaliacao",
                               {"nota_nps": 10, "nota_buffet": 5, "nota_espera": 5, "nota_atendimento": 5})
            self.assertEqual(s, 201)
            return r
        return self.chamar("GET", f"/api/jornadas/{codigo}")[1]

    def test_fidelidade_por_celular(self):
        cel = "11977770001"
        r = self.visita_completa(self.nova_intencao(celular=cel)[1]["codigo"])
        self.assertEqual((r["cadastro"], r["visitas_cliente"], r["pontos_cliente"]), (True, 1, 1))
        r = self.visita_completa(self.nova_intencao(celular=cel)[1]["codigo"], avaliar=False)
        self.assertEqual((r["visitas_cliente"], r["pontos_cliente"]), (2, 1))  # ponto só com avaliação
        with closing(app.conectar()) as banco:
            linha = banco.execute("SELECT visitas, pontos FROM fidelidade WHERE celular = ?", (cel,)).fetchone()
        self.assertEqual(tuple(linha), (2, 1))
        s, f = self.chamar("GET", f"/api/clientes/{cel}", cookie=self.gerente)
        self.assertEqual((s, f), (200, {"visitas": 2, "pontos": 1}))

    def test_completar_cadastro_do_espontaneo(self):
        s, v = self.chamar("POST", "/api/visitas", {}, self.atendente)
        self.assertEqual((v["cadastro"], v["visitas_cliente"], v["pontos_cliente"]), (False, None, None))
        rota = f"/api/jornadas/{v['codigo']}/cadastro"
        self.assertEqual(self.chamar("POST", rota, {"nome": "Ana", "celular": "11977770002"})[0], 400)  # sem LGPD
        s, r = self.chamar("POST", rota, {"nome": "Ana Nova", "celular": "(11) 97777-0002", "aceite_lgpd": True})
        self.assertEqual((s, r["cadastro"], r["visitas_cliente"], r["pontos_cliente"]), (200, True, 0, 0))
        self.assertEqual(self.chamar("POST", rota, {"nome": "Outra", "celular": "11977770009", "aceite_lgpd": True})[0], 409)
        r = self.visita_completa(v["codigo"])
        self.assertEqual((r["visitas_cliente"], r["pontos_cliente"]), (1, 1))

        # Celular que já existe (veio de uma visita planejada): usa o cliente existente.
        cel = "11977770003"
        self.visita_completa(self.nova_intencao(celular=cel)[1]["codigo"])
        s, v2 = self.chamar("POST", "/api/visitas", {}, self.atendente)
        s, r = self.chamar("POST", f"/api/jornadas/{v2['codigo']}/cadastro", {"nome": "Nome Diferente", "celular": cel, "aceite_lgpd": True})
        self.assertEqual((r["visitas_cliente"], r["pontos_cliente"]), (1, 1))  # já traz o histórico
        with closing(app.conectar()) as banco:
            clientes = banco.execute("SELECT nome FROM cliente WHERE celular = ?", (cel,)).fetchall()
        self.assertEqual([c["nome"] for c in clientes], ["Cliente Teste"])  # um só cadastro, nome mantido
        # Visita planejada já tem cadastro.
        planejada = self.nova_intencao(celular="11977770004")[1]
        self.assertTrue(planejada["cadastro"])
        self.assertEqual(self.chamar("POST", f"/api/jornadas/{planejada['codigo']}/cadastro",
                                     {"nome": "X Y", "celular": "11977770005", "aceite_lgpd": True})[0], 409)

    def test_tv_cozinha_e_salao(self):
        self.assertEqual(self.chamar("GET", "/api/dashboard/tv", cookie=self.atendente)[0], 403)
        logo = (app.agora() + timedelta(minutes=20)).astimezone(app.SP)
        mesmo_dia = logo.date() == app.hoje_local()  # perto da meia-noite, +20 min já é amanhã
        s, _ = self.chamar("POST", "/api/intencoes", {"horario_previsto": logo.isoformat(), "pessoas": 4,
                                                      "pratos": self.pratos[:1] if mesmo_dia else [],
                                                      "nome": "Grupo", "celular": "11977770006", "aceite_lgpd": True})
        self.assertEqual(s, 201)
        s, aberta = self.chamar("POST", "/api/visitas", {}, self.atendente)  # fica na casa
        self.visita_completa(self.chamar("POST", "/api/visitas", {}, self.atendente)[1]["codigo"], mesa=77, avaliar=False)
        self.visita_completa(self.chamar("POST", "/api/visitas", {}, self.atendente)[1]["codigo"], mesa=78, avaliar=False)
        self.visita_completa(self.chamar("POST", "/api/visitas", {}, self.atendente)[1]["codigo"], mesa=78, avaliar=False)
        self.visita_completa(self.chamar("POST", "/api/visitas", {}, self.atendente)[1]["codigo"], avaliar=False)  # sem mesa

        s, t = self.chamar("GET", "/api/dashboard/tv", cookie=self.gerente)
        self.assertEqual(s, 200)
        if mesmo_dia:
            self.assertGreaterEqual(t["previstas_proxima_hora"], 4)
        self.assertGreaterEqual(t["na_casa"]["visitas"], 1)
        self.assertIsNotNone(t["prato_top"])
        self.assertIn(aberta["codigo"], [v["codigo"] for v in t["em_curso"]])
        mesas = [m["mesa"] for m in t["mesas_limpeza"]]
        self.assertEqual((mesas.count(77), mesas.count(78)), (1, 1))  # uma linha por mesa
        self.assertTrue(all(m["minutos"] == 0 for m in t["mesas_limpeza"] if m["mesa"] in (77, 78)))

        # Depois da janela de limpeza (45 min), a mesa some da lista.
        with closing(app.conectar()) as banco:
            depois = app.agora() + app.JANELA_LIMPEZA + timedelta(minutes=1)
            antes = app.agora() + app.JANELA_LIMPEZA - timedelta(minutes=1)
            with mock.patch.object(app, "agora", return_value=antes):
                self.assertIn(77, [m["mesa"] for m in app.painel_tv(banco)["mesas_limpeza"]])
            with mock.patch.object(app, "agora", return_value=depois):
                t = app.painel_tv(banco)
        self.assertNotIn(77, [m["mesa"] for m in t["mesas_limpeza"]])
        aberta_tv = next(v for v in t["em_curso"] if v["codigo"] == aberta["codigo"])
        self.assertTrue(aberta_tv["acima_media"])  # em curso há 46 min > permanência média (~0 min)

    def test_mesas_no_modo_demonstracao(self):
        """Com agora simulado (12:40): mesa do seed medida pelas 12:40, mesa ao vivo pelo relógio real."""
        hoje = app.hoje_local()
        base = datetime.combine(hoje, datetime.min.time(), app.SP)
        with closing(app.conectar()) as banco:
            try:
                banco.execute("INSERT OR REPLACE INTO parametro VALUES ('dados_simulados', '1')")
                banco.execute("INSERT OR REPLACE INTO parametro VALUES ('demo_agora', '12:40')")
                for codigo, saida, mesa in (("BOV-SEED", base.replace(hour=12, minute=30), 501),
                                            ("BOV-MADR", base.replace(minute=25), 502),
                                            ("BOV-NOIT", base.replace(hour=20, minute=55), 503)):
                    banco.execute("""INSERT INTO visita (codigo, origem, check_in_em, check_out_em, mesa)
                                     VALUES (?, 'espontaneo', ?, ?, ?)""",
                                  (codigo, app.iso(saida - timedelta(minutes=20)), app.iso(saida), mesa))
                for real, esperado in ((base.replace(minute=30), {501: 10, 502: 5}),      # madrugada
                                       (base.replace(hour=21), {501: 10, 503: 5})):        # noite
                    with mock.patch.object(app, "agora", return_value=real), \
                            mock.patch.dict(app.os.environ, {}, clear=False):
                        app.os.environ.pop("DEMO_AGORA", None)
                        mesas = {m["mesa"]: m["minutos"] for m in app.painel_tv(banco)["mesas_limpeza"] if m["mesa"] > 500}
                    self.assertEqual(mesas, esperado, real)
            finally:
                banco.rollback()

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
