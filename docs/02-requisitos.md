# Requisitos

Requisitos funcionais e não funcionais **implementados** no MVP. Cada item pode ser conferido na aplicação
(`python app.py`) e na suíte automatizada `testes.py`.

## Requisitos funcionais

| ID | Requisito |
| --- | --- |
| RF01 | O cliente escolhe dia, horário de chegada e até 3 pratos de interesse do cardápio do dia |
| RF02 | O cliente informa nome, celular (com consentimento LGPD) e número de pessoas |
| RF03 | O sistema gera um código único de visita (`BOV-XXXX`) com QR code |
| RF04 | O cliente acompanha a visita pelo código, digitado ou lido por QR (câmera ou foto) |
| RF05 | O cliente espontâneo recebe um código no totem de entrada, sem usar o app |
| RF06 | O totem imprime um comprovante com o código e o QR |
| RF07 | A equipe registra check-in, buffet concluído (opcional) e check-out pelo terminal |
| RF08 | O check-out aceita o número da mesa (opcional) |
| RF09 | O terminal detecta uma intenção de outro dia e oferece registrar como espontâneo |
| RF10 | O cliente avalia a visita após o check-out: NPS 0–10, notas 1–5 (buffet, espera, atendimento) e comentário |
| RF11 | Cada avaliação vale 1 ponto de fidelidade para o cliente identificado pelo celular |
| RF12 | O espontâneo completa o cadastro depois, pelo código da visita |
| RF13 | O dashboard mostra visitas do dia, pessoas no salão, conversão, permanência, NPS, chegadas previstas × reais, pratos mais desejados e funil dos planejados |
| RF14 | O dashboard tem a aba Análise do período (tendências, insights por regras, satisfação, comentários, recorrência, CSV) |
| RF15 | A TV Cozinha mostra pessoas previstas na próxima hora, prato mais desejado, pessoas na casa e tempo médio até a balança |
| RF16 | A TV Salão mostra pessoas na casa, permanência média com destaque para quem já passou dela, previstas na próxima hora e mesas aguardando limpeza |
| RF17 | O gerente cadastra, edita e remove pratos do cardápio do dia e copia o cardápio do dia anterior |

## Requisitos não funcionais

| ID | Requisito |
| --- | --- |
| RNF01 | Stack simples: Python (biblioteca padrão) + SQLite + HTML/CSS/JS, sem frameworks no app |
| RNF02 | Sem dependência de CDN: bibliotecas de terceiros ficam em `vendor/` |
| RNF03 | Horários gravados em UTC (ISO 8601) e exibidos no horário de São Paulo |
| RNF04 | Códigos sem caracteres ambíguos (sem 0/O e 1/I) |
| RNF05 | Visita sem check-out em 3 horas é encerrada automaticamente (`saida_estimada = 1`) e fica fora das médias |
| RNF06 | Intenção sem check-in até o horário previsto + 30 min conta como não comparecimento |
| RNF07 | O terminal aceita leitor de QR/código de barras e digitação manual |
| RNF08 | Telas responsivas para celular, tablet (terminal) e TV (tela cheia) |
| RNF09 | Login da equipe com papéis: o atendente não acessa dashboard nem cardápio |
| RNF10 | Senhas com PBKDF2-SHA256 e bloqueio temporário após 5 tentativas erradas |
