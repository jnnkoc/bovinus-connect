# Jornada e telas

Mapa das telas do cliente e da equipe e a jornada completa, planejada e espontânea.

![Jornada do cliente](diagramas/jornada.svg)

O **código da visita** é o fio condutor: nasce na intenção (app) ou no totem (espontâneo) e é o mesmo até a
avaliação. A avaliação só é liberada depois do check-out.

## Telas do cliente

| Tela | Rota | O que mostra |
| --- | --- | --- |
| Início | `/` | Boas-vindas, cardápio do dia por categoria, atalhos para planejar, acompanhar e avaliar |
| Planejar visita | `/#planejar` | Dia, horário, até 3 pratos de interesse, nº de pessoas, nome, celular, LGPD |
| Código da visita | `/#codigo` | Código `BOV-XXXX` + QR, resumo da intenção, "Acompanhar minha visita" |
| Minha visita | `/minha-visita?codigo=...` | Check-in → buffet → check-out, completar cadastro (espontâneo), visitas e pontos, botão Avaliar |
| Avaliar | `/avaliar?codigo=...` | NPS 0–10, notas 1–5 (buffet, espera, atendimento), comentário; ao enviar, mostra visitas e pontos |

## Telas da equipe

| Tela | Rota | Papel | O que mostra |
| --- | --- | --- | --- |
| Login | `/login` | atendente, gerente | Usuário e senha |
| Terminal | `/terminal` | atendente, gerente | Modos Entrada, Balança e Caixa; QR ou digitação; espontâneo e comprovante |
| Dashboard | `/dashboard` | gerente | Aba Hoje, aba Análise do período, Modo TV (Cozinha e Salão) |
| Cardápio do dia | `/cardapio` | gerente | Pratos do dia, cadastro e edição, copiar do dia anterior, prévia do app |

## Jornada passo a passo

1. **Planejado:** o cliente planeja pelo app e recebe o código. **Espontâneo:** toca em "Sou cliente espontâneo" no
   totem e recebe o código na tela (e no comprovante impresso, se quiser).
2. **Check-in** no terminal de entrada (o espontâneo já entra com check-in feito).
3. **Buffet concluído** na balança (opcional).
4. **Check-out** no caixa, com o número da mesa (opcional). A mesa aparece na TV Salão como "aguardando limpeza".
5. **Minha visita:** o espontâneo pode completar o cadastro (nome, celular, LGPD) para ganhar fidelidade.
6. **Avaliação:** NPS e notas por tema; cada avaliação soma 1 ponto ao celular do cliente.

## Todas as capturas

Capturas da aplicação rodando com o banco de demonstração (**dados simulados**). Clique para ampliar.

### Cliente

| | | |
| --- | --- | --- |
| [![Início](../prints/01-cliente-inicio.png)](../prints/01-cliente-inicio.png) | [![Planejar visita](../prints/02-cliente-planejar.png)](../prints/02-cliente-planejar.png) | [![Código + QR](../prints/03-cliente-codigo.png)](../prints/03-cliente-codigo.png) |
| Início | Planejar visita | Código + QR |
| [![Minha visita (antes do check-in)](../prints/04-minha-visita-antes.png)](../prints/04-minha-visita-antes.png) | [![Visita concluída](../prints/14-minha-visita-concluida.png)](../prints/14-minha-visita-concluida.png) | [![Completar cadastro](../prints/17-minha-visita-cadastro.png)](../prints/17-minha-visita-cadastro.png) |
| Minha visita (antes do check-in) | Visita concluída | Completar cadastro |
| [![Fidelidade](../prints/18-minha-visita-fidelidade.png)](../prints/18-minha-visita-fidelidade.png) | [![Avaliação](../prints/15-avaliar.png)](../prints/15-avaliar.png) | [![Pontos após avaliar](../prints/16-avaliar-obrigado.png)](../prints/16-avaliar-obrigado.png) |
| Fidelidade | Avaliação | Pontos após avaliar |

### Terminal

| | | |
| --- | --- | --- |
| [![Entrada](../prints/05-terminal-entrada.png)](../prints/05-terminal-entrada.png) | [![Check-in feito](../prints/06-terminal-checkin.png)](../prints/06-terminal-checkin.png) | [![Balança](../prints/07-terminal-balanca.png)](../prints/07-terminal-balanca.png) |
| Entrada | Check-in feito | Balança |
| [![Buffet concluído](../prints/08-terminal-balanca-ok.png)](../prints/08-terminal-balanca-ok.png) | [![Caixa com mesa](../prints/09-terminal-caixa.png)](../prints/09-terminal-caixa.png) | [![Saída registrada](../prints/10-terminal-caixa-ok.png)](../prints/10-terminal-caixa-ok.png) |
| Buffet concluído | Caixa com mesa | Saída registrada |
| [![Espontâneo](../prints/11-terminal-espontaneo.png)](../prints/11-terminal-espontaneo.png) | [![Comprovante](../prints/12-comprovante.png)](../prints/12-comprovante.png) | [![Saída do espontâneo](../prints/13-terminal-caixa-espontaneo.png)](../prints/13-terminal-caixa-espontaneo.png) |
| Espontâneo | Comprovante | Saída do espontâneo |

### Gestão

| | | |
| --- | --- | --- |
| [![Login da equipe](../prints/19-login.png)](../prints/19-login.png) | [![Dashboard · Hoje](../prints/20-dashboard-hoje.png)](../prints/20-dashboard-hoje.png) | [![Dashboard · Hoje (página inteira)](../prints/21-dashboard-hoje-completo.png)](../prints/21-dashboard-hoje-completo.png) |
| Login da equipe | Dashboard · Hoje | Dashboard · Hoje (página inteira) |
| [![Análise do período](../prints/22-dashboard-analise.png)](../prints/22-dashboard-analise.png) | [![Análise (página inteira)](../prints/23-dashboard-analise-completo.png)](../prints/23-dashboard-analise-completo.png) | [![Escolha da TV](../prints/24-tv-escolha.png)](../prints/24-tv-escolha.png) |
| Análise do período | Análise (página inteira) | Escolha da TV |
| [![Cardápio do dia](../prints/25-cardapio.png)](../prints/25-cardapio.png) | [![TV Cozinha](../prints/26-tv-cozinha.png)](../prints/26-tv-cozinha.png) | [![TV Salão](../prints/27-tv-salao.png)](../prints/27-tv-salao.png) |
| Cardápio do dia | TV Cozinha | TV Salão |
