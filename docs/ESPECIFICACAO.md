# Bovinu's Connect — MVP do Hackathon (FMU/FIAM)

## Contexto
Hackathon com a Bovinu's Grill & Beer, Unidade Augusta (São Paulo). Escopo: **serviço do almoço por quilo** e a **jornada do cliente** (se servir e ser atendido).
**Fora do escopo** (não criar nada disso): operação da cozinha/compras/estoque, pagamento, pedidos, preços por prato, jantar, outras unidades, mudança da forma de trabalho (ex.: à la carte).

Dores apresentadas pelo restaurante:
1. Mix do prato: sabem o peso, não sabem o que foi servido.
2. Filas e tempo do cliente: buffet, churrasqueira, atendimento na mesa.
3. Limpeza do salão: quanto tempo a mesa fica suja após a saída.
4. Qualidade da comida: sobras, pratos que não saem do buffet, comentários.
O restaurante quase não tem indicadores da jornada; o ticket médio é uma das principais referências.

Casa: 3 salões (Inferior ~20 mesas, Principal ~30, Superior ~40), duas saídas com caixa (principal e auxiliar).

## A solução
Uma plataforma integrada, um banco único, várias telas. Dois tipos de cliente:
- **Planejado**: usa o app antes de ir (intenção com pratos e horário).
- **Espontâneo**: chega sem o app e recebe um código na entrada.

Diferencial: a intenção do cliente vira **previsão de demanda do buffet** (horário e pratos), comparada com o que acontece de fato na operação.

Login da equipe: telas `/terminal` (gerente e atendente), `/cardapio` e `/dashboard` (só gerente) exigem login; as telas do cliente são públicas.

Próximos passos (NÃO construir agora): foto do prato na balança com IA, chamado de garçom, benefícios de fidelidade, outras unidades.

## Telas

Referências visuais em `docs/referencias/`. Use como **inspiração de layout e cores**, aplicando as correções desta seção. **Não reproduzir fotos nem fundo de fogo**: usar cores sólidas. Logo: usar arquivo oficial se existir em `docs/referencias/logo.*`; senão, o nome "Bovinu's Grill & Beer" em texto. O logo oficial está em `docs/referencias/logo.png` e é servido por `img/logo.png` (recortado na elipse pelo CSS `.logo`).

### 1. App do cliente (`cliente.html`, rota `/`) — ref. `cliente-app.png`, `cliente-site.png`
Uma única versão web, mobile-first (não fazer site e app separados).
- **Início**: cardápio do dia + botão "Planejar visita" + "Minha visita".
- **Planejar**: categorias (Churrasco, Acompanhamento, Salada, Sobremesa) que abrem os pratos do dia para marcar (**até 3 pratos de interesse**); horário previsto; nº de pessoas; nome e celular com aceite LGPD.
- **Código da visita**: código grande (formato `BOV-XXXX`) + QR. Texto: "Mostre este código na entrada".
- **Minha visita (acompanhamento)**: o cliente digita o código e **só vê** o status (Aguardando chegada → Visita em andamento → Visita encerrada), atualizando sozinho. **O cliente nunca registra check-in, buffet ou saída pelo app.**
- **Fidelidade**: "Você já veio X vezes" (contagem por celular, só visitas com check-out).
- **Avaliação** (`avaliar.html`): disponível após o check-out, pelo código (planejado ou espontâneo).
  - Pergunta principal NPS: "De 0 a 10, quanto você recomendaria a Bovinu's a um amigo?"
  - Notas por tema de 1 a 5: Buffet (variedade, qualidade, reposição), Espera, Atendimento.
  - Comentário opcional.

### 2. Terminal (`terminal.html`, rota `/terminal`) — ref. `terminal.png`
Uma tela com **modo** selecionável no topo. **O sistema registra automaticamente a próxima etapa** da visita: ninguém escolhe a etapa. Fluxo: ler/digitar código → confirmação por 2 segundos → volta ao início.
- **Modo Entrada (totem do cliente)**: "Usar código do app" (QR ou digitar) → check-in. "Sou cliente espontâneo" → cria visita e mostra o código **grande** com o aviso "Guarde este código para a saída e para avaliar". Intenção marcada para **outro dia** não faz check-in: mostra "Esta visita está marcada para DD/MM" e o botão "Registrar como espontâneo".
- **Modo Caixa (equipe)**: ler/digitar código → check-out. Campo opcional de nº da mesa.
- **Modo Balança (opcional)**: ler/digitar código → buffet concluído.
O buffet é opcional: o check-out funciona sem ele.

### 3. Cardápio do dia (`cardapio.html`, rota `/cardapio`) — ref. `cardapio.png`
- Selecionar a data; listar os pratos do dia; adicionar, editar e remover.
- Campos do prato: nome, categoria, descrição curta, destaque (sim/não), vegetariano (sim/não).
- Botão "Copiar cardápio do dia anterior".
- Imagem fixa por categoria (sem upload de foto).
- **Remover do mockup**: menu "Pedidos", peso/preço, horário de jantar, seletor de unidades, o aviso amarelo de rodapé.

### 4. Dashboard (`dashboard.html`, rota `/dashboard`) — ref. `dashboard.png`
Menu lateral apenas com: Dashboard, Cardápio do dia, Terminal (e Mesas, se existir). Topo: seletor de data, selo **"Dados simulados"**, horário da última atualização. Atualiza a cada 10 s.

**Aba Hoje (ao vivo)**
- Cartões: visitas do dia (planejados × espontâneos), clientes no salão agora, conversão da intenção, permanência média, NPS.
- **Gráfico principal: chegadas previstas (intenções) × chegadas reais por 15 min** (barras reais + linha prevista).
- Próximas chegadas previstas (ex.: "12h30–13h: 23 pessoas").
- Ranking de pratos mais desejados hoje.
- Funil **só dos planejados**: intenção → check-in → check-out → avaliação. Espontâneos aparecem à parte. A base são **todas** as intenções do dia, inclusive as que ainda vão chegar; abaixo do funil aparece a composição (já chegaram · ainda por chegar · não compareceram).
- Botão "Modo TV" (opcional): tela cheia com 3 números grandes — clientes no salão, chegadas previstas na próxima meia hora, prato mais desejado.

**Aba Análise (período)**
- Tendência diária de visitas, conversão e permanência.
- Pratos sempre pouco desejados.
- Satisfação por tema (médias 1–5) + comentários recentes.
- Recorrência de clientes.
- Tabela de visitas recentes (código, origem, chegada, saída, tempo, NPS) + "Exportar CSV".
- Insights do período: frases geradas **por regras sobre os dados** (ex.: maior pico, prato mais desejado). Nunca texto fixo.

**Remover do mockup**: páginas Visitas/Clientes/Avaliações/Relatórios/Configurações, estrelas na avaliação, "Permanência" como etapa do funil, bloco "Tempo por etapa".

### 5. Mesas (`mesas.html`, rota `/mesas`) — opcional, se der tempo
Mapa simples dos 3 salões. No check-out com nº de mesa, a mesa vira "suja" com cronômetro; o garçom toca em "limpa". Indicador "tempo médio de mesa suja" no dashboard.

## Modelo de dados (alvo)
- `cliente`: id, nome, celular (único), consentimento_em
- `prato`: id, nome, categoria (`churrasco`, `acompanhamento`, `salada`, `sobremesa`), descricao, vegetariano
- `cardapio_dia`: data, prato_id, destaque
- `intencao`: id, codigo, cliente_id, horario_previsto, pessoas, criada_em
- `intencao_prato`: intencao_id, prato_id
- `visita`: id, codigo, origem (`planejado` | `espontaneo`), intencao_id (opcional, único), cliente_id (opcional), check_in_em, buffet_concluido_em (opcional), check_out_em, mesa (opcional), saida_estimada (0/1)
- `avaliacao`: visita_id, nota_nps (0–10), nota_buffet, nota_espera, nota_atendimento (1–5), comentario
- `mesa` (opcional): numero, salao, status, suja_desde

Planejado: o código da intenção vira o código da visita no check-in. Espontâneo: o código é gerado no terminal.

## Stack (não trocar)
- Python 3.10+ só com biblioteca padrão (`http.server` + `sqlite3`). **Não adicionar dependências Python.**
- Frontend: HTML + CSS + JavaScript puro, um arquivo por tela, servido pelo `app.py` (mesma origem). Bibliotecas JS só se necessárias (ex.: QR) e salvas localmente em `vendor/`, nunca por CDN.
- Banco: SQLite (`schema.sql`). Horários em UTC ISO 8601; exibidos em `America/Sao_Paulo`.
- Rodar: `python app.py` (Windows: `py app.py`) → http://127.0.0.1:8000

## Estrutura
- `app.py` — servidor e API REST (contrato no README.md)
- `schema.sql` — tabelas e views
- `seed.py` — dados simulados
- `cliente.html`, `avaliar.html`, `terminal.html`, `cardapio.html`, `dashboard.html`, `mesas.html`
- `estilo.css` — estilo compartilhado
- `comum.js` — utilitários JS compartilhados (API, formatação, menu lateral)
- `img/` — logo oficial
- `iniciar.bat` — atalho para Windows (cria dados simulados se faltar o banco e sobe o servidor)
- `login.html` — login da equipe · `usuarios.py` — gerenciar usuários · `testes.py` — testes automatizados (`py testes.py`)
- `vendor/` — bibliotecas JS locais (`qrcode.js`, `jsQR.js`; ver `vendor/LEIAME.md`)
- `docs/` — documentação de entrega e `docs/referencias/` (mockups)

## Identidade visual
Bordô/vermelho escuro como cor principal, fundo creme, destaque âmbar/dourado (tons aproximados dos mockups). Uma única fonte em todas as telas. Botões grandes; nas telas de equipe e totem, alvos de toque bem grandes.

## Regras de trabalho
- **Uma etapa por vez.** Antes de mudanças grandes, apresente o plano e espere aprovação.
- Prefira a solução **mais simples** que funcione na demo.
- Ao mudar a API, atualize o contrato no README.md.
- Toda mudança no banco vai no `schema.sql` e precisa funcionar num banco novo (apagar `bovinus.db` para testar).
- Telas mobile-first. Ações da equipe com no máximo **um toque ou uma leitura**.
- Dados simulados sempre identificados na interface. Datas simuladas recentes (relativas a hoje).
- `DEMO_AGORA` (padrão 12:40; topo do `seed.py` e variável de ambiente do `app.py`): fora do almoço (11h–15h), com dados simulados, é o "agora" da aba Hoje; o seed gera hoje entre 11h e esse horário, com intenções futuras até 14h45.
- Textos em português do Brasil.
- Depois de cada etapa, diga exatamente como testar.
- Nunca inventar números de negócio da Bovinu's; parâmetros da simulação ficam no topo do `seed.py`, fáceis de ajustar.

## Definição dos indicadores
- **Conversão da intenção** = intenções com check-in ÷ intenções cujo horário previsto + 30 min já passou. (Só planejados.)
- **Planejados × espontâneos** = visitas por origem.
- **No salão agora** = visitas com check-in e sem check-out (excluindo saída estimada).
- **Permanência** = check-out − check-in (só visitas com check-out real).
- **Tempo até a balança** = buffet concluído − check-in (só quando registrado).
- **NPS** = % notas 9–10 − % notas 0–6, só com avaliações recebidas.
- **Satisfação por tema** = média das notas 1–5 de buffet, espera e atendimento.
- **Recorrência** = visitas com check-out por cliente (celular) no período.
- **Chegadas previstas × reais** = soma de pessoas das intenções por 15 min × check-ins por 15 min.
- **Pratos desejados** = nº de intenções que marcaram cada prato no dia.
- **Tempo de mesa suja** (opcional) = marcada limpa − check-out da visita da mesa.
- Visita sem check-out após 3 h: fechada automaticamente com `saida_estimada = 1` e excluída da permanência.
- Intenção sem check-in até horário previsto + 30 min: conta como não convertida.
