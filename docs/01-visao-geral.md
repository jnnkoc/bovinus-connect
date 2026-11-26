# Bovinu's Connect — Visão geral

Projeto acadêmico do Hackathon FMU 2026.2 para a Bovinu's Grill & Beer (Unidade Augusta, almoço por quilo).
Equipe: Janaina Costa, Vitor Nunes e Matheus Vaccari.

Uma plataforma única que acompanha a jornada do almoço por quilo, do lado do cliente e do lado da equipe, com a
**intenção de visita** como diferencial: o cliente avisa antes de chegar e a casa ganha previsibilidade.

## Problema

Dores apresentadas no desafio:

| # | Dor | Descrição |
| --- | --- | --- |
| i | Mix do prato | A casa sabe o peso vendido, mas não sabe o que o cliente queria encontrar no buffet |
| ii | Filas e tempo | Filas se formam no buffet, na churrasqueira e no caixa, sem medição |
| iii | Limpeza | Não há registro de quando uma mesa ficou livre e precisa ser limpa |
| iv | Qualidade | Opiniões e comentários dos clientes não são capturados de forma estruturada |

## Objetivo e diferencial

Um app para o cliente e um terminal + dashboard para a equipe, compartilhando o mesmo banco de dados.

O diferencial é a **intenção de visita**: antes de chegar, o cliente informa o horário previsto, quantas pessoas vêm e
até 3 pratos de interesse. Isso dá à casa uma estimativa de demanda que hoje ela não tem.

> Os pratos marcados são **preferência declarada**, não consumo efetivo: o sistema não mede o que foi servido no prato.

## Escopo do MVP (implementado)

- Jornada do cliente: planejar → check-in → buffet (opcional) → check-out → avaliar
- Clientes planejados (pelo app) e espontâneos (código gerado no totem)
- Terminal da equipe com três modos: Entrada, Balança (opcional) e Caixa
- Comprovante impresso com código e QR
- Acompanhamento da visita ("Minha visita") e cadastro posterior do espontâneo
- Fidelidade simples: visitas e pontos por celular
- Dashboard gerencial (Hoje e Análise do período, exportação CSV) e Modo TV (Cozinha e Salão)
- Cardápio do dia e login da equipe com papéis (gerente e atendente)

## Fora do escopo

- Cozinha, compras e controle de estoque
- Sistemas de pagamento
- Mudança na forma de trabalho da casa
- Outras unidades além da Augusta

## Próximos passos e evolução (não implementados)

O MVP já guarda o código da visita, o celular com consentimento, a mesa e os horários da jornada; cada fase reaproveita
essa base.

- **Fase 2 · Relacionamento:** fidelidade robusta (níveis, benefícios e resgate de pontos, no padrão de grandes redes de
  franquias) e comunicação segmentada com os clientes, com consentimento, em todas as unidades.
- **Fase 3 · Salão conectado:** tablet na mesa para chamar o garçom, PDV mobile para anotar pedidos (com visão mais fina
  de demanda e limpeza) e integração com balanças inteligentes para dados de pratos e cubas nos dashboards.
- **Fase 4 · Reservas para grupos:** espaço reservado para grandes equipes, com número de mesas definido.

## Sobre os dados

Todos os números exibidos nas telas vêm de **dados simulados** gerados pelo `seed.py` (parâmetros documentados no
próprio arquivo). Nenhum número representa resultado real da Bovinu's. O MVP não foi testado em operação no restaurante.

## Indicadores

| Indicador | Fórmula |
| --- | --- |
| Conversão da intenção | intenções com check-in ÷ intenções cujo horário previsto + 30 min já passou |
| Permanência | check-out − check-in (só visitas com check-out real) |
| Até a balança | buffet concluído − check-in |
| NPS | % de notas 9–10 − % de notas 0–6 |
| Notas por tema | média das notas 1–5 de buffet, espera e atendimento |
| Recorrência | visitas com check-out, agrupadas por celular |
| Previsto × real | pessoas nas intenções × check-ins, a cada 15 min |
| Mesas aguardando limpeza | último check-out com mesa informada, nos últimos 45 min |
