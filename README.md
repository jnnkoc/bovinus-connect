# Bovinu’s Augusta — Dados e integração

## Executar

1. Extraia todos os arquivos do ZIP para uma pasta.
2. Abra um terminal nessa pasta e execute `py app.py` no Windows ou `python3 app.py` no Linux/macOS. É necessário Python 3.10 ou mais recente. Nenhum pacote extra é necessário.
3. Abra http://127.0.0.1:8000 no navegador. O banco `bovinus.db` será criado automaticamente na pasta do projeto.
4. Abra **Gerar visita de teste**, preencha o horário previsto e copie o código. Na mesma tela você já pode registrar chegada, primeira pesagem e saída. Para recuperar a visita depois, use **Buscar**.

O terminal mostra os horários no fuso de São Paulo. O campo de teste interpreta o horário previsto no fuso configurado no navegador.

## Banco SQLite

- `intencao` guarda o código único e o horário previsto.
- `visita` usa como chave primária a chave estrangeira para `intencao`. Cada intenção pode gerar uma visita, criada no check-in.
- `avaliacao` guarda até uma resposta por visita.
- A view `jornada` inclui intenções sem check-in para o cálculo da conversão.

A API grava horários em UTC no formato ISO 8601 e registra as etapas na ordem chegada → primeira pesagem → saída. Repetir uma etapa retorna o registro anterior com o mesmo horário. O código digitável tem 12 caracteres hexadecimais.

## Contrato para as outras frentes

| Método e rota | Corpo JSON | Uso |
| --- | --- | --- |
| POST /api/intencoes | `{"horario_previsto":"2026-11-25T12:30:00-03:00"}` | O site cria a intenção e exibe o campo `codigo_visita` da resposta (201). |
| GET /api/jornadas/{codigo} | — | Consulta a visita pelo código. |
| POST /api/jornadas/{codigo}/check-in | `{}` | Confirma a chegada. |
| POST /api/jornadas/{codigo}/buffet | `{}` | Registra a primeira pesagem. |
| POST /api/jornadas/{codigo}/check-out | `{}` | Registra a saída. |
| POST /api/jornadas/{codigo}/avaliacao | `{"nota_nps":9,"comentario":"Bom atendimento"}` | Registra a avaliação após a saída. O comentário é opcional. |
| GET /api/jornadas | — | Entrega ao painel a lista de todas as intenções, com os dados da visita quando houver. |

Cada registro contém `codigo_visita`, `horario_previsto`, `check_in_em`, `buffet_concluido_em`, `check_out_em`, `nota_nps` e `comentario`. Campos ainda sem registro retornam `null`. As operações bem-sucedidas retornam 200, exceto a criação da intenção. Os erros retornam um objeto com o campo `erro`. Código desconhecido gera 404 e etapa fora de ordem gera 409.

Para a integração local, sirva as telas pela mesma origem do backend ou encaminhe as chamadas `/api` pelo servidor do frontend. O protótipo escuta apenas no próprio computador e foi preparado para demonstração local com dados fictícios. A publicação exigirá controle de acesso às operações do terminal e à listagem do painel.

## Leitura para o painel

- Use check-in até primeira pesagem para medir o percurso completo da entrada à balança. Esse intervalo inclui a escolha dos alimentos e eventuais esperas.
- Use check-in até check-out para medir a permanência.
- Calcule a conversão a partir das intenções cujo período de chegada já terminou e conte quantas têm check-in.
- Calcule o NPS somente com as avaliações recebidas.
