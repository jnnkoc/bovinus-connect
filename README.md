# Bovinu's Connect — MVP do Hackathon (FMU)

Aplicação web responsiva que liga a **intenção de visita** do cliente do almoço self-service da Bovinu's Grill & Beer
(Unidade Augusta) aos registros de **chegada, buffet, saída e satisfação**, alimentando um **dashboard gerencial**.

> Os números exibidos vêm de `seed.py` e são **dados simulados** (identificados na interface). Nenhum número é dado real da Bovinu's.

## Como rodar

Requisito: **Python 3.10+** (só biblioteca padrão, nenhum pacote extra).

```bash
py seed.py      # (opcional) apaga e recria bovinus.db com dados simulados
py app.py       # inicia o servidor
```

No Linux/macOS use `python3`. No Windows também dá para dar dois cliques em **`iniciar.bat`**: ele cria os dados simulados
se o banco não existir, abre o dashboard e sobe o servidor.

Abra http://127.0.0.1:8000. O servidor também aceita conexões da rede local e mostra, ao iniciar, o endereço para abrir
**no celular na mesma rede Wi-Fi** (o Windows pode pedir permissão no firewall na primeira vez).
Variáveis opcionais: `BOVINUS_PORTA` (padrão 8000), `BOVINUS_HOST` (padrão `0.0.0.0`; use `127.0.0.1` para só este computador)
e `BOVINUS_BANCO` (caminho do arquivo SQLite).

## Telas

| Rota | Arquivo | Para quem | O que faz |
| --- | --- | --- | --- |
| `/` | `cliente.html` | Cliente (celular) | Cardápio do dia, **Planejar visita** (dia, horário, até 3 pratos, pessoas, nome, celular e aceite LGPD) → código `BOV-XXXX`; **Minha visita** (só acompanha o status, atualiza a cada 10 s, "Você já veio X vezes") |
| `/avaliar` | `avaliar.html` | Cliente | Após a saída: NPS 0–10 + notas 1–5 de Buffet, Espera e Atendimento + comentário |
| `/terminal` | `terminal.html` | Totem e equipe | Modos **Entrada** (check-in pelo código ou "Sou cliente espontâneo"), **Balança** (buffet concluído, opcional) e **Caixa** (check-out + mesa opcional). O sistema registra a etapa do modo; confirmação de 2 s e volta ao início. `?modo=caixa` abre direto no modo |
| `/cardapio` | `cardapio.html` | Gerente | Cardápio por data: adicionar, editar, remover, destaque, vegetariano, copiar do dia anterior, prévia do app |
| `/dashboard` | `dashboard.html` | Gerente | **Hoje (ao vivo)**: cartões, chegadas previstas × reais por 15 min, próximas chegadas, pratos desejados, funil dos planejados, Modo TV. **Análise**: tendências, insights por regras, satisfação, comentários, recorrência, pratos pouco desejados, visitas recentes, exportar CSV |

## Fluxo da demonstração

1. `py seed.py` e `py app.py`.
2. `/cardapio`: confira o cardápio de hoje (ou copie o do dia anterior).
3. `/` no celular: **Planejar visita** → anote o código `BOV-XXXX`.
4. `/terminal?modo=entrada`: digite o código → check-in. Teste também **Sou cliente espontâneo**.
5. `/terminal?modo=balanca` (opcional) e `/terminal?modo=caixa` → saída.
6. `/avaliar?codigo=BOV-XXXX` → avaliação.
7. `/dashboard`: veja os números mudarem (atualiza a cada 10 s).

## Banco (SQLite, `schema.sql`)

`cliente` · `prato` · `cardapio_dia` · `intencao` · `intencao_prato` · `visita` · `avaliacao` · `parametro`, e a view `jornada`.

- Horários gravados em **UTC ISO 8601**; exibidos em `America/Sao_Paulo` (UTC−3 fixo, sem horário de verão).
- `visita` tem código próprio e `origem` (`planejado` | `espontaneo`). No planejado, o código da intenção vira o código da visita no check-in.
- O **buffet é opcional**: o check-out só exige o check-in.
- Visita aberta há mais de 3 h é fechada com `saida_estimada = 1` e fica fora da permanência média.
- Códigos `BOV-XXXX` sem 0/O e 1/I, únicos entre intenções e visitas.
- `PRAGMA user_version = 2`. Se existir um `bovinus.db` da versão anterior, o `app.py` o renomeia para `bovinus.db.v1.bak` e cria um novo.

## Contrato da API

Corpo e respostas em JSON. Erros retornam `{"erro": "mensagem"}` com 400 (dados inválidos), 404 (não encontrado) ou 409 (conflito ou etapa fora de ordem).
O código aceita `BOV-ABCD`, `bov-abcd` ou só `ABCD`.

| Método e rota | Corpo | Resposta |
| --- | --- | --- |
| `GET /api/cardapio?data=AAAA-MM-DD` | — | `{data, pratos:[{id, nome, categoria, descricao, vegetariano, destaque}]}` (sem `data` = hoje) |
| `POST /api/cardapio/{data}` | `{nome, categoria, descricao?, vegetariano?, destaque?}` | 201 + cardápio do dia |
| `PUT /api/cardapio/{data}/{prato_id}` | mesmos campos | cardápio do dia |
| `DELETE /api/cardapio/{data}/{prato_id}` | — | cardápio do dia (o prato sai só daquele dia) |
| `POST /api/cardapio/{data}/copiar-anterior` | — | cardápio do dia + `copiado_de` |
| `POST /api/intencoes` | `{horario_previsto, pessoas, pratos:[ids, até 3], nome, celular, aceite_lgpd:true}` | 201 + visita |
| `POST /api/visitas` | — | 201 + visita espontânea já com check-in |
| `GET /api/jornadas/{codigo}` | — | visita (sem dados pessoais) |
| `POST /api/jornadas/{codigo}/proxima` | `{modo: "entrada" \| "balanca" \| "caixa", mesa?}` | `{etapa, repetido, horario, mensagem, visita}` |
| `POST /api/jornadas/{codigo}/avaliacao` | `{nota_nps 0–10, nota_buffet, nota_espera, nota_atendimento 1–5, comentario?}` | 201 + visita |
| `GET /api/clientes/{celular}` | — | `{visitas}` (visitas com check-out) |
| `GET /api/dashboard/hoje?data=` | — | cartões, série por 15 min, próximas chegadas, pratos, funil |
| `GET /api/dashboard/analise?inicio=&fim=` | — | resumo, dias, satisfação, comentários, recorrência, pratos pouco desejados, recentes, insights (padrão: últimos 7 dias) |
| `GET /api/visitas.csv?inicio=&fim=` | — | CSV (`;`, UTF-8 com BOM para o Excel) |

**Visita** = `{codigo, origem, status: "aguardando" | "em_andamento" | "encerrada", horario_previsto, pessoas, pratos:[nomes],
check_in_em, buffet_concluido_em, check_out_em, saida_estimada, mesa, avaliada, visitas_cliente}`.

**`/proxima`**: em `entrada`, faz o check-in; em `balanca`, registra o buffet (exige check-in); em `caixa`, registra o check-out
(exige check-in; substitui uma saída estimada). Repetir uma etapa não altera nada e devolve `repetido: true` com o horário original.

## Indicadores

Definições em `docs/ESPECIFICACAO.md` ("Definição dos indicadores"): conversão da intenção (só planejados, após previsto + 30 min),
planejados × espontâneos, no salão agora, permanência (só check-out real), tempo até a balança, NPS, satisfação por tema,
recorrência por celular, chegadas previstas (pessoas) × reais (check-ins) por 15 min e pratos desejados.

## Segurança e privacidade (limites do MVP)

- Protótipo para demonstração local com dados fictícios: **não há login**. Antes de publicar, proteger `/terminal`,
  `/cardapio`, `/dashboard` e as rotas de escrita e de painel.
- A consulta pública da visita não devolve nome nem celular. O celular só é usado para contar visitas, com aceite LGPD registrado.

## Próximos passos (fora deste MVP)

QR code no app e leitura pela câmera no terminal (bibliotecas locais em `vendor/`), mapa de mesas com tempo de mesa suja,
foto do prato na balança com IA, chamado de garçom, benefícios de fidelidade e outras unidades.
