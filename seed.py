"""Apaga e recria bovinus.db com DADOS SIMULADOS para a demonstração.

Nenhum número aqui é dado real da Bovinu's: são parâmetros de simulação, ajustáveis abaixo.
Rodar:  py seed.py   (Windows)   |   python3 seed.py
"""
import random
import sys
from collections import Counter
from contextlib import closing
from datetime import datetime, time, timedelta, timezone

import app

# ============================================================ PARÂMETROS DA SIMULAÇÃO
SEMENTE = 42                    # mesma semente = mesmos dados
DIAS_UTEIS = 5                  # últimos N dias úteis até hoje (hoje sempre entra)
CARDAPIO_PROXIMO_DIA_UTIL = True  # já deixa o cardápio do próximo dia útil cadastrado
VISITAS_POR_DIA = 200           # média de visitas por dia
VARIACAO_DIARIA = 0.15          # ± 15% entre os dias
ALMOCO_INICIO = time(11, 0)
ALMOCO_FIM = time(15, 0)
PICO = time(12, 30)             # horário de pico das chegadas
DESVIO_CHEGADA_MIN = 45         # espalhamento das chegadas em torno do pico (minutos)
FRACAO_PLANEJADOS = 0.30        # visitas que vieram de uma intenção no app
FRACAO_NAO_COMPARECIMENTO = 0.10  # intenções sem check-in
CLIENTES_RECORRENTES = 40       # clientes que voltam vários dias
FRACAO_PLANEJADOS_RECORRENTES = 0.5  # parte dos planejados que vem desse grupo
FRACAO_COM_BUFFET = 0.85        # visitas com "buffet concluído" registrado na balança
BALANCA_MIN = (8, 20)           # minutos entre check-in e balança (mín, máx)
PERMANENCIA_MEDIA_MIN = 55
PERMANENCIA_DESVIO_MIN = 15
FRACAO_SEM_CHECKOUT = 0.02      # esquecidos no caixa (serão fechados como saída estimada)
FRACAO_COM_MESA = 0.6           # check-outs com nº de mesa informado
MESAS = 90
FRACAO_AVALIACOES = 0.25        # visitas encerradas que avaliam
PESSOAS_PESOS = {1: 35, 2: 35, 3: 15, 4: 10, 5: 3, 6: 2}
PRATOS_POR_INTENCAO_PESOS = {1: 30, 2: 35, 3: 35}  # máximo 3 pratos
VIES_TEMA = {"buffet": 0.1, "espera": -0.5, "atendimento": 0.3}  # deslocamento das notas 1–5 por tema
# Se agora estiver fora do almoço, a simulação de HOJE é deslocada como se fossem 12h45,
# para o dashboard ao vivo ter visitas em andamento e intenções futuras.
HORA_SIMULADA_FORA_DO_ALMOCO = time(12, 45)
# Usuários de DEMONSTRAÇÃO para as telas da equipe. Só para a apresentação: troque antes de usar de verdade.
USUARIOS_DEMO = [
    ("gerente", "Gerente (demo)", "gerente", "bovinus-demo"),
    ("atendente", "Atendente (demo)", "atendente", "terminal-demo"),
]

# Catálogo de pratos: (nome, categoria, descrição, vegetariano, popularidade relativa, fixo no cardápio)
CATALOGO = [
    ("Picanha", "churrasco", "Fatiada na hora, direto da churrasqueira.", 0, 10, True),
    ("Fraldinha", "churrasco", "Corte macio, assado lentamente.", 0, 6, True),
    ("Linguiça toscana", "churrasco", "Linguiça artesanal na brasa.", 0, 4, False),
    ("Coxinha da asa", "churrasco", "Temperada com ervas e limão.", 0, 4, False),
    ("Costela bovina", "churrasco", "Costela assada por horas.", 0, 7, False),
    ("Maminha", "churrasco", "Corte suculento com sal grosso.", 0, 5, False),
    ("Cupim", "churrasco", "Assado lentamente até desmanchar.", 0, 3, False),
    ("Arroz branco", "acompanhamento", "Arroz soltinho.", 1, 5, True),
    ("Feijão carioca", "acompanhamento", "Feijão temperado da casa.", 0, 5, True),
    ("Farofa da casa", "acompanhamento", "Farofa com bacon e ovos.", 0, 3, False),
    ("Batata frita", "acompanhamento", "Crocante por fora, macia por dentro.", 1, 7, False),
    ("Mandioca cozida", "acompanhamento", "Mandioca na manteiga.", 1, 2, False),
    ("Arroz biro-biro", "acompanhamento", "Arroz com bacon, ovos e batata palha.", 0, 4, False),
    ("Feijão tropeiro", "acompanhamento", "Feijão com linguiça, bacon e farofa.", 0, 5, False),
    ("Purê de batata", "acompanhamento", "Cremoso, com manteiga.", 1, 2, False),
    ("Legumes grelhados", "acompanhamento", "Abobrinha, berinjela e pimentão.", 1, 1, False),
    ("Salada verde", "salada", "Folhas da estação.", 1, 3, True),
    ("Salada Caesar", "salada", "Alface, croutons, parmesão e molho Caesar.", 0, 4, False),
    ("Vinagrete", "salada", "Tomate, cebola e pimentão.", 1, 3, False),
    ("Salpicão", "salada", "Frango desfiado com legumes e batata palha.", 0, 3, False),
    ("Tabule", "salada", "Trigo, hortelã, tomate e limão.", 1, 1, False),
    ("Salada de grão-de-bico", "salada", "Grão-de-bico com ervas.", 1, 1, False),
    ("Pudim de leite", "sobremesa", "Pudim de leite condensado.", 1, 5, True),
    ("Mousse de maracujá", "sobremesa", "Leve e azedinha.", 1, 3, False),
    ("Abacaxi com canela", "sobremesa", "Grelhado na brasa.", 1, 2, False),
    ("Brigadeirão", "sobremesa", "Brigadeiro de colher, cremoso.", 1, 3, False),
]
POR_CATEGORIA_NO_DIA = {"churrasco": 5, "acompanhamento": 6, "salada": 3, "sobremesa": 2}  # ~16 pratos

NOMES = ["Ana", "Bruno", "Camila", "Diego", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela",
         "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia", "Paulo", "Rafaela", "Samuel",
         "Tatiane", "Vinícius", "Beatriz", "Caio", "Débora", "Fernanda", "Gustavo", "Larissa",
         "Marcelo", "Natália", "Renato", "Sofia", "Thiago", "Vanessa"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Lima", "Pereira", "Costa", "Almeida",
              "Ferreira", "Rodrigues", "Gomes", "Martins", "Araújo", "Barbosa", "Ribeiro", "Carvalho"]
COMENTARIOS = {
    "bom": ["Picanha no ponto, voltarei!", "Buffet bem variado e reposição rápida.",
            "Atendimento muito atencioso.", "Ótimo custo-benefício para o almoço.",
            "Gostei de poder ver o cardápio antes de vir.", "Ambiente agradável e comida quente."],
    "medio": ["Boa comida, mas a fila da balança estava grande.", "Faltou reposição de saladas no pico.",
              "Demorou um pouco para liberar mesa.", "Gostaria de mais opções vegetarianas."],
    "ruim": ["Esperei muito na churrasqueira.", "Alguns pratos estavam frios.",
             "Mesa demorou para ser limpa.", "Atendimento demorado no caixa."],
}
# ====================================================================================

rnd = random.Random(SEMENTE)


def escolher_pesos(pesos):
    return rnd.choices(list(pesos), weights=list(pesos.values()))[0]


def dias_simulados(hoje):
    dias, d = [hoje], hoje - timedelta(days=1)
    while len(dias) < DIAS_UTEIS:
        if d.weekday() < 5:
            dias.append(d)
        d -= timedelta(days=1)
    return sorted(dias)


def momento_chegada(dia):
    inicio = datetime.combine(dia, ALMOCO_INICIO, app.SP)
    fim = datetime.combine(dia, ALMOCO_FIM, app.SP) - timedelta(minutes=15)
    pico = datetime.combine(dia, PICO, app.SP)
    while True:
        m = pico + timedelta(minutes=rnd.gauss(0, DESVIO_CHEGADA_MIN))
        if inicio <= m <= fim:
            return m


def criar_celular(usados):
    while True:
        cel = "119" + "".join(rnd.choice("0123456789") for _ in range(8))
        if cel not in usados:
            usados.add(cel)
            return cel


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if app.BANCO.exists():
        app.BANCO.unlink()
    app.preparar_banco(criar_usuarios=False)
    agora_real = app.agora()
    hoje = agora_real.astimezone(app.SP).date()
    hora_local = agora_real.astimezone(app.SP).time()
    if ALMOCO_INICIO <= hora_local <= ALMOCO_FIM:
        deslocamento = timedelta(0)
    else:
        deslocamento = (agora_real - datetime.combine(hoje, HORA_SIMULADA_FORA_DO_ALMOCO, app.SP))
        # mantém o almoço deslocado dentro do mesmo dia
        deslocamento = max(timedelta(hours=-11), min(timedelta(hours=9), deslocamento))
    contagem = Counter()

    with closing(app.conectar()) as banco, banco:
        banco.execute("INSERT INTO parametro (chave, valor) VALUES ('dados_simulados', '1')")
        for login, nome, papel, senha in USUARIOS_DEMO:
            app.criar_usuario(banco, login, nome, papel, senha)
        ids_pratos = {}
        for nome, cat, desc, veg, _, _ in CATALOGO:
            ids_pratos[nome] = banco.execute(
                "INSERT INTO prato (nome, categoria, descricao, vegetariano) VALUES (?, ?, ?, ?)",
                (nome, cat, desc, veg)).lastrowid
        popularidade = {nome: pop for nome, _, _, _, pop, _ in CATALOGO}

        celulares = set()
        recorrentes = []
        for _ in range(CLIENTES_RECORRENTES):
            nome = f"{rnd.choice(NOMES)} {rnd.choice(SOBRENOMES)}"
            recorrentes.append((nome, criar_celular(celulares)))

        def cliente_id(nome, celular, momento):
            banco.execute(
                """INSERT INTO cliente (nome, celular, consentimento_em) VALUES (?, ?, ?)
                   ON CONFLICT(celular) DO NOTHING""", (nome, celular, app.iso(momento)))
            return banco.execute("SELECT id FROM cliente WHERE celular = ?", (celular,)).fetchone()[0]

        codigos = set()

        def novo_codigo():
            while True:
                c = "BOV-" + "".join(rnd.choice(app.ALFABETO) for _ in range(4))
                if c not in codigos:
                    codigos.add(c)
                    return c

        def montar_cardapio(dia):
            """Cardápio do dia: fixos + sorteio por categoria."""
            cardapio = []
            for cat, qtd in POR_CATEGORIA_NO_DIA.items():
                itens = [c for c in CATALOGO if c[1] == cat]
                fixos = [c[0] for c in itens if c[5]]
                outros = [c[0] for c in itens if not c[5]]
                cardapio += fixos + rnd.sample(outros, min(qtd - len(fixos), len(outros)))
            destaques = set(rnd.sample(cardapio, 2))
            for nome in cardapio:
                banco.execute("INSERT INTO cardapio_dia (data, prato_id, destaque) VALUES (?, ?, ?)",
                              (dia.isoformat(), ids_pratos[nome], int(nome in destaques)))
                contagem["itens de cardápio"] += 1
            return cardapio

        # Cardápio já cadastrado para o próximo dia útil (sem visitas), para planejar na demo.
        proximo = hoje + timedelta(days=1)
        while proximo.weekday() >= 5:
            proximo += timedelta(days=1)
        if CARDAPIO_PROXIMO_DIA_UTIL:
            montar_cardapio(proximo)

        for dia in dias_simulados(hoje):
            e_hoje = dia == hoje
            ajuste = deslocamento if e_hoje else timedelta(0)
            corte = agora_real  # nada acontece depois de agora
            cardapio = montar_cardapio(dia)

            total = round(VISITAS_POR_DIA * (1 + rnd.uniform(-VARIACAO_DIARIA, VARIACAO_DIARIA)))
            planejados = round(total * FRACAO_PLANEJADOS)
            n_intencoes = round(planejados / (1 - FRACAO_NAO_COMPARECIMENTO))
            hoje_recorrentes = rnd.sample(recorrentes, min(len(recorrentes),
                                                            round(planejados * FRACAO_PLANEJADOS_RECORRENTES)))

            jornadas = [("planejado", i) for i in range(n_intencoes)] + \
                       [("espontaneo", i) for i in range(total - planejados)]
            for origem, indice in jornadas:
                chegada = momento_chegada(dia) + ajuste
                intencao_id = cli = None
                codigo = novo_codigo()
                if origem == "planejado":
                    previsto = app.faixa_de(chegada)  # cliente escolhe horário em múltiplos de 15 min
                    criada = previsto - timedelta(minutes=rnd.randint(30, 60 * 30))
                    if criada > corte:
                        continue
                    if indice < len(hoje_recorrentes):
                        nome, cel = hoje_recorrentes[indice]
                    else:
                        nome, cel = f"{rnd.choice(NOMES)} {rnd.choice(SOBRENOMES)}", criar_celular(celulares)
                    cli = cliente_id(nome, cel, criada)
                    intencao_id = banco.execute(
                        """INSERT INTO intencao (codigo, cliente_id, horario_previsto, pessoas, criada_em)
                           VALUES (?, ?, ?, ?, ?)""",
                        (codigo, cli, app.iso(previsto), escolher_pesos(PESSOAS_PESOS), app.iso(criada))).lastrowid
                    contagem["intenções"] += 1
                    n_pratos = escolher_pesos(PRATOS_POR_INTENCAO_PESOS)
                    escolhidos = set()
                    while len(escolhidos) < n_pratos:
                        escolhidos.add(rnd.choices(cardapio, weights=[popularidade[p] for p in cardapio])[0])
                    banco.executemany("INSERT INTO intencao_prato VALUES (?, ?)",
                                      [(intencao_id, ids_pratos[p]) for p in escolhidos])
                    if rnd.random() < FRACAO_NAO_COMPARECIMENTO:
                        contagem["intenções sem comparecimento"] += 1
                        continue
                    chegada = previsto + timedelta(minutes=rnd.gauss(3, 8))

                if chegada > corte:
                    if origem == "planejado":
                        contagem["intenções futuras (hoje)"] += 1
                    continue
                buffet = (chegada + timedelta(minutes=rnd.uniform(*BALANCA_MIN))
                          if rnd.random() < FRACAO_COM_BUFFET else None)
                permanencia = max(25, min(120, rnd.gauss(PERMANENCIA_MEDIA_MIN, PERMANENCIA_DESVIO_MIN)))
                saida = chegada + timedelta(minutes=permanencia)
                if buffet and buffet > saida:
                    buffet = None
                if rnd.random() < FRACAO_SEM_CHECKOUT:
                    saida = None
                if buffet and buffet > corte:
                    buffet = None
                if saida and saida > corte:
                    saida = None
                mesa = rnd.randint(1, MESAS) if saida and rnd.random() < FRACAO_COM_MESA else None
                visita_id = banco.execute(
                    """INSERT INTO visita (codigo, origem, intencao_id, cliente_id, check_in_em,
                                           buffet_concluido_em, check_out_em, mesa)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (codigo, origem, intencao_id, cli, app.iso(chegada),
                     buffet and app.iso(buffet), saida and app.iso(saida), mesa)).lastrowid
                contagem["visitas planejadas" if origem == "planejado" else "visitas espontâneas"] += 1
                if not saida:
                    contagem["visitas abertas"] += 1

                if saida and rnd.random() < FRACAO_AVALIACOES:
                    avaliada = saida + timedelta(minutes=rnd.randint(2, 240))
                    if avaliada > corte:
                        continue
                    nps = rnd.choices(range(11), weights=[1, 1, 1, 1, 2, 2, 4, 8, 16, 22, 30])[0]
                    base = 1 + nps * 0.4

                    def nota(tema):
                        return max(1, min(5, round(base + VIES_TEMA[tema] + rnd.gauss(0, 0.7))))
                    tom = "bom" if nps >= 9 else "medio" if nps >= 7 else "ruim"
                    comentario = rnd.choice(COMENTARIOS[tom]) if rnd.random() < 0.4 else ""
                    banco.execute(
                        """INSERT INTO avaliacao (visita_id, nota_nps, nota_buffet, nota_espera,
                                                  nota_atendimento, comentario, criada_em)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (visita_id, nps, nota("buffet"), nota("espera"), nota("atendimento"), comentario, app.iso(avaliada)))
                    contagem["avaliações"] += 1

        app.fechar_visitas_antigas(banco)
        contagem["clientes"] = banco.execute("SELECT COUNT(*) FROM cliente").fetchone()[0]
        contagem["saídas estimadas (fechadas após 3 h)"] = banco.execute(
            "SELECT COUNT(*) FROM visita WHERE saida_estimada = 1").fetchone()[0]

    print(f"Banco recriado com DADOS SIMULADOS: {app.BANCO.name}")
    print(f"Dias: {', '.join(d.strftime('%d/%m') for d in dias_simulados(hoje))}")
    if deslocamento:
        print(f"Agora está fora do almoço: o dia de hoje foi simulado como se fossem "
              f"{HORA_SIMULADA_FORA_DO_ALMOCO.strftime('%Hh%M')} (horários deslocados).")
    for chave, valor in sorted(contagem.items()):
        print(f"  {chave}: {valor}")
    print("Usuários de DEMONSTRAÇÃO (troque com: py usuarios.py senha <login>):")
    for login, _, papel, senha in USUARIOS_DEMO:
        print(f"  {login} / {senha}  ({papel})")


if __name__ == "__main__":
    main()
