// Conteúdo do site. Tudo aqui descreve o que está implementado no MVP, salvo onde marcado como hipótese ou próximo passo.
export const REPO = 'https://github.com/jnnkoc/bovinus-connect';
export const DOCS = REPO + '/blob/main/docs/';

export const EQUIPE = ['Janaina Costa', 'Vitor Nunes', 'Matheus Vaccari'];

export const NAV = [
  ['problema', 'Problema'],
  ['jornada', 'Jornada'],
  ['telas', 'Telas'],
  ['indicadores', 'Indicadores'],
  ['arquitetura', 'Arquitetura'],
  ['documentacao', 'Docs'],
  ['evolucao', 'Evolução'],
  ['midia', 'Equipe'],
];

export const FATOS = [
  ['5', 'telas para o cliente'],
  ['4', 'telas para a equipe'],
  ['2', 'TVs de operação'],
  ['21', 'testes automatizados'],
];

export const DORES = [
  {
    n: '01', titulo: 'Mix do prato',
    dor: 'A casa sabe o peso vendido, mas não sabe o que o cliente queria encontrar no buffet.',
    resposta: 'Na intenção de visita, o cliente marca até 3 pratos de interesse. O dashboard mostra o ranking do dia — preferência declarada, não consumo.',
  },
  {
    n: '02', titulo: 'Filas e tempo',
    dor: 'Filas no buffet, na churrasqueira e no caixa acontecem sem nenhuma medição.',
    resposta: 'Check-in, balança e caixa registram horários. Viram tempo até a balança, permanência e chegadas previstas × reais a cada 15 minutos.',
  },
  {
    n: '03', titulo: 'Limpeza de mesas',
    dor: 'Não há registro de quando uma mesa ficou livre e precisa ser limpa.',
    resposta: 'O caixa informa a mesa no check-out e a TV Salão lista "Mesa 4 — há 12 min" por 45 minutos.',
  },
  {
    n: '04', titulo: 'Qualidade percebida',
    dor: 'Opiniões e comentários dos clientes não são capturados de forma estruturada.',
    resposta: 'Avaliação com NPS, notas de buffet, espera e atendimento e comentário. Cada avaliação vale 1 ponto de fidelidade.',
  },
];

export const JORNADAS = {
  planejado: {
    rotulo: 'Planejado (pelo app)',
    passos: [
      { titulo: 'Planeja a visita', texto: 'Escolhe dia, horário, pessoas e até 3 pratos de interesse, com consentimento LGPD.', tela: '02-cliente-planejar', onde: 'App do cliente' },
      { titulo: 'Recebe o código', texto: 'Um código BOV-XXXX com QR. É o mesmo do começo ao fim da visita.', tela: '03-cliente-codigo', onde: 'App do cliente' },
      { titulo: 'Check-in na entrada', texto: 'O totem lê o QR (ou o código digitado) e registra a chegada.', tela: '06-terminal-checkin', onde: 'Terminal · Entrada' },
      { titulo: 'Buffet na balança', texto: 'Etapa opcional: marca quando o cliente terminou de se servir.', tela: '08-terminal-balanca-ok', onde: 'Terminal · Balança' },
      { titulo: 'Check-out no caixa', texto: 'Registra a saída e, se informada, a mesa — que entra na lista de limpeza.', tela: '09-terminal-caixa', onde: 'Terminal · Caixa' },
      { titulo: 'Acompanha e avalia', texto: 'Em "Minha visita", vê as etapas, as visitas e os pontos. Depois avalia.', tela: '14-minha-visita-concluida', onde: 'App do cliente' },
    ],
  },
  espontaneo: {
    rotulo: 'Espontâneo (sem app)',
    passos: [
      { titulo: 'Chega sem avisar', texto: 'No totem, toca em "Sou cliente espontâneo".', tela: '05-terminal-entrada', onde: 'Terminal · Entrada' },
      { titulo: 'Recebe código e QR', texto: 'O check-in já é feito. O código aparece na tela.', tela: '11-terminal-espontaneo', onde: 'Terminal · Entrada' },
      { titulo: 'Imprime o comprovante', texto: '"Guarde este código — use para avaliar sua visita depois."', tela: '12-comprovante', onde: 'Impressora do totem' },
      { titulo: 'Check-out no caixa', texto: 'Mesmo fluxo do planejado, com mesa opcional.', tela: '13-terminal-caixa-espontaneo', onde: 'Terminal · Caixa' },
      { titulo: 'Completa o cadastro', texto: 'Em "Minha visita", informa nome e celular (LGPD) para ganhar fidelidade.', tela: '17-minha-visita-cadastro', onde: 'App do cliente' },
      { titulo: 'Ganha visitas e pontos', texto: 'A visita passa a contar para o celular. Avaliar soma 1 ponto.', tela: '18-minha-visita-fidelidade', onde: 'App do cliente' },
    ],
  },
};

// tipo: celular | desktop | tv | papel
export const TELAS = [
  { id: '01-cliente-inicio', grupo: 'Cliente', titulo: 'Início do app', desc: 'Cardápio do dia e atalhos para planejar, acompanhar e avaliar.', tipo: 'celular' },
  { id: '02-cliente-planejar', grupo: 'Cliente', titulo: 'Planejar visita', desc: 'Dia, horário, pratos de interesse e pessoas.', tipo: 'celular' },
  { id: '03-cliente-codigo', grupo: 'Cliente', titulo: 'Código da visita', desc: 'Código BOV-XXXX com QR para a entrada.', tipo: 'celular' },
  { id: '04-minha-visita-antes', grupo: 'Cliente', titulo: 'Minha visita', desc: 'Acompanhamento antes do check-in.', tipo: 'celular' },
  { id: '14-minha-visita-concluida', grupo: 'Cliente', titulo: 'Visita concluída', desc: 'Etapas, visitas e pontos de fidelidade.', tipo: 'celular' },
  { id: '17-minha-visita-cadastro', grupo: 'Cliente', titulo: 'Completar cadastro', desc: 'O espontâneo liga a visita ao celular.', tipo: 'celular' },
  { id: '15-avaliar', grupo: 'Cliente', titulo: 'Avaliação', desc: 'NPS, notas por tema e comentário.', tipo: 'celular' },
  { id: '16-avaliar-obrigado', grupo: 'Cliente', titulo: 'Pontos após avaliar', desc: '"Você já veio X vezes" e "Você tem Y pontos".', tipo: 'celular' },
  { id: '05-terminal-entrada', zoom: 2, foco: '50% 45%', grupo: 'Totem', titulo: 'Entrada', desc: 'Check-in por QR ou código, ou cliente espontâneo.', tipo: 'desktop' },
  { id: '06-terminal-checkin', zoom: 2, foco: '50% 45%', grupo: 'Totem', titulo: 'Check-in feito', desc: 'Confirmação com opção de comprovante.', tipo: 'desktop' },
  { id: '07-terminal-balanca', zoom: 2, foco: '50% 45%', grupo: 'Totem', titulo: 'Balança', desc: 'Marca o fim do buffet (opcional).', tipo: 'desktop' },
  { id: '09-terminal-caixa', zoom: 2, foco: '50% 45%', grupo: 'Totem', titulo: 'Caixa', desc: 'Check-out com número da mesa.', tipo: 'desktop' },
  { id: '11-terminal-espontaneo', zoom: 2, foco: '50% 45%', grupo: 'Totem', titulo: 'Espontâneo', desc: 'Código gerado na hora, com QR.', tipo: 'desktop' },
  { id: '12-comprovante', grupo: 'Totem', titulo: 'Comprovante', desc: 'Bobina de 80 mm com código e QR.', tipo: 'papel' },
  { id: '20-dashboard-hoje', grupo: 'Gestão', titulo: 'Dashboard · Hoje', desc: 'Visitas, salão, conversão, permanência, NPS e chegadas.', tipo: 'desktop' },
  { id: '22-dashboard-analise', grupo: 'Gestão', titulo: 'Análise do período', desc: 'Insights por regras, tendências e satisfação.', tipo: 'desktop' },
  { id: '25-cardapio', grupo: 'Gestão', titulo: 'Cardápio do dia', desc: 'Cadastro de pratos com prévia do app.', tipo: 'desktop' },
  { id: '19-login', zoom: 2, foco: '50% 45%', grupo: 'Gestão', titulo: 'Login da equipe', desc: 'Papéis gerente e atendente.', tipo: 'desktop' },
  { id: '24-tv-escolha', grupo: 'TVs', titulo: 'Escolha da TV', desc: 'Cozinha ou Salão, antes da tela cheia.', tipo: 'desktop' },
  { id: '26-tv-cozinha', grupo: 'TVs', titulo: 'TV Cozinha', desc: 'Previstas na próxima hora, prato mais desejado, casa e balança.', tipo: 'tv' },
  { id: '27-tv-salao', grupo: 'TVs', titulo: 'TV Salão', desc: 'Permanência, acima da média e mesas aguardando limpeza.', tipo: 'tv' },
];

// Telas usadas só na jornada (não aparecem na galeria).
export const TELAS_JORNADA = [
  { id: '08-terminal-balanca-ok', grupo: 'Totem', titulo: 'Buffet concluído', desc: 'Confirmação da balança.', tipo: 'desktop' },
  { id: '13-terminal-caixa-espontaneo', grupo: 'Totem', titulo: 'Saída do espontâneo', desc: 'Check-out com a mesa.', tipo: 'desktop' },
  { id: '18-minha-visita-fidelidade', grupo: 'Cliente', titulo: 'Fidelidade', desc: 'Visitas e pontos após o cadastro.', tipo: 'celular' },
];

export const INDICADORES = [
  { nome: 'Conversão da intenção', formula: 'intenções com check-in ÷ intenções cujo horário + 30 min já passou', uso: 'Mostra se quem avisa realmente vem.' },
  { nome: 'Chegadas previstas × reais', formula: 'pessoas nas intenções × check-ins, a cada 15 min', uso: 'Compara o pico anunciado com o pico real.' },
  { nome: 'Tempo até a balança', formula: 'buffet concluído − check-in', uso: 'Proxy do tempo de fila e de serviço.' },
  { nome: 'Permanência média', formula: 'check-out − check-in (sem saídas estimadas)', uso: 'Base para o destaque "acima da média" na TV Salão.' },
  { nome: 'Pratos mais desejados', formula: 'nº de intenções que marcaram cada prato', uso: 'Preferência declarada para orientar a reposição.' },
  { nome: 'NPS e notas por tema', formula: '% notas 9–10 − % notas 0–6; média 1–5 de buffet, espera e atendimento', uso: 'Mostra onde a experiência perde pontos.' },
  { nome: 'Recorrência', formula: 'visitas com check-out agrupadas por celular', uso: 'Quantos clientes identificados voltam.' },
  { nome: 'Mesas aguardando limpeza', formula: 'último check-out com mesa nos últimos 45 min', uso: 'Lista operacional para o salão.' },
];

// Ganhos esperados: hipóteses, não resultados medidos.
export const GANHOS = [
  {
    eixo: 'Eficiência', icone: '⚡',
    itens: [
      'Cozinha vê quantas pessoas são esperadas na próxima hora antes de elas chegarem.',
      'Salão recebe a lista de mesas recém-liberadas, em vez de procurar mesa por mesa.',
      'Tempos de entrada, balança e caixa passam a ser medidos em vez de estimados.',
    ],
  },
  {
    eixo: 'Financeiro', icone: '💰',
    itens: [
      'Reposição orientada pelos pratos mais desejados pode reduzir sobra e falta no buffet.',
      'Pratos de baixo interesse aparecem na análise como candidatos a troca.',
      'Fidelidade por celular cria base para campanhas de retorno — sem custo de app nativo.',
    ],
  },
  {
    eixo: 'Gestão', icone: '📊',
    itens: [
      'Indicadores de jornada além do ticket médio, num só painel.',
      'Insights automáticos por regras e exportação CSV para análises próprias.',
      'Voz do cliente estruturada por tema: buffet, espera e atendimento.',
    ],
  },
];

export const TECNOLOGIAS = [
  ['Python 3', 'Servidor HTTP e API REST com a biblioteca padrão'],
  ['SQLite', 'Banco local com views jornada e fidelidade'],
  ['HTML · CSS · JS', 'Uma página por tela, sem framework no app'],
  ['QR code', 'Geração e leitura local (vendor/), sem CDN'],
  ['PBKDF2', 'Senhas com hash e bloqueio após 5 erros'],
  ['unittest', '21 testes cobrindo jornada, regras e indicadores'],
];

export const DOCUMENTOS = [
  { titulo: 'Visão geral', desc: 'Problema, objetivo, escopo, indicadores e natureza dos dados.', md: '01-visao-geral.md', pdf: '01-visao-geral.pdf' },
  { titulo: 'Requisitos', desc: '17 requisitos funcionais e 10 não funcionais implementados.', md: '02-requisitos.md', pdf: '02-requisitos.pdf' },
  { titulo: 'Jornada e telas', desc: 'Telas do cliente e da equipe e a jornada passo a passo.', md: '03-jornada-e-telas.md', pdf: '03-jornada-e-telas.pdf' },
  { titulo: 'Diagramas e DER', desc: 'Casos de uso, DER e dicionário de dados conferidos com o schema.', md: '04-diagramas-e-der.md', pdf: '04-diagramas-e-der.pdf' },
];

// Evolução planejada (nada aqui está implementado). Cada item aponta o que do MVP ele reaproveita.
export const FASES = [
  {
    id: 'f1', fase: 'Fase 1', titulo: 'MVP atual', status: 'implementado',
    resumo: 'A base que já funciona e que todas as próximas fases reaproveitam.',
    itens: [
      { ic: '🎟️', t: 'Código único da visita', d: 'Intenção pelo app ou código no totem, do check-in à avaliação.' },
      { ic: '📱', t: 'Celular com consentimento', d: 'Cliente identificado pelo celular, com aceite LGPD registrado.' },
      { ic: '🍽️', t: 'Mesa e horários da jornada', d: 'Check-in, balança, check-out e mesa alimentam dashboard e TVs.' },
      { ic: '⭐', t: 'Fidelidade simples', d: 'Visitas e pontos por celular, calculados no banco.' },
    ],
  },
  {
    id: 'f2', fase: 'Fase 2', titulo: 'Relacionamento', status: 'planejado',
    resumo: 'Transformar a fidelidade simples em um programa de relacionamento para toda a rede.',
    itens: [
      { ic: '💎', t: 'Fidelidade robusta', d: 'Níveis, benefícios e resgate de pontos, no padrão dos programas de grandes redes de franquias.', base: 'visitas e pontos por celular (view fidelidade)' },
      { ic: '📣', t: 'Comunicação com o cliente', d: 'Campanhas e mensagens segmentadas por frequência e preferência, com consentimento, em todas as unidades da rede.', base: 'celular com aceite LGPD e pratos de interesse' },
    ],
  },
  {
    id: 'f3', fase: 'Fase 3', titulo: 'Salão conectado', status: 'planejado',
    resumo: 'Levar o sistema para a mesa e para as mãos da equipe, com dados mais precisos.',
    itens: [
      { ic: '📲', t: 'Tablet na mesa', d: 'O cliente chama o garçom pelo tablet e o chamado chega à equipe com o número da mesa.', base: 'mesa registrada na visita e TV Salão' },
      { ic: '🧾', t: 'PDV mobile', d: 'Garçons anotam pedidos no celular ou tablet, e a gestão ganha visão mais fina de demanda e de mesas a limpar.', base: 'terminal web com papéis e lista de limpeza' },
      { ic: '⚖️', t: 'Balanças inteligentes', d: 'Integração com balanças e cubas inteligentes para medir pratos e reposição, alimentando os dashboards com dados precisos.', base: 'etapa Balança e tempo até a balança' },
    ],
  },
  {
    id: 'f4', fase: 'Fase 4', titulo: 'Reservas para grupos', status: 'planejado',
    resumo: 'Um produto novo para empresas e grandes equipes, sobre a mesma base.',
    itens: [
      { ic: '🗓️', t: 'Espaço reservado para equipes', d: 'Grandes grupos reservam um espaço dedicado, com número de mesas definido para a ocasião.', base: 'intenção de visita com horário e nº de pessoas' },
    ],
  },
];
