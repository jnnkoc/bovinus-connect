// Bovinu's Connect — utilitários compartilhados pelas telas.
const FUSO = 'America/Sao_Paulo';

const CATEGORIAS = {
  churrasco: { nome: 'Churrasco', icone: '🥩' },
  acompanhamento: { nome: 'Acompanhamento', icone: '🍚' },
  salada: { nome: 'Salada', icone: '🥗' },
  sobremesa: { nome: 'Sobremesa', icone: '🍮' },
};

async function api(rota, { metodo, dados } = {}) {
  const opcoes = { method: metodo || (dados === undefined ? 'GET' : 'POST'), headers: {} };
  if (dados !== undefined) {
    opcoes.headers['Content-Type'] = 'application/json';
    opcoes.body = JSON.stringify(dados);
  }
  let resposta;
  try {
    resposta = await fetch(rota, opcoes);
  } catch {
    throw new Error('Sem conexão com o servidor.');
  }
  const resultado = await resposta.json().catch(() => ({}));
  // Tela da equipe com sessão vencida: volta para o login.
  if (resposta.status === 401 && document.body.hasAttribute('data-equipe')) {
    location.href = '/login?volta=' + encodeURIComponent(location.pathname + location.search + location.hash);
    throw new Error('Sessão encerrada. Faça login novamente.');
  }
  if (!resposta.ok) {
    const erro = new Error(resultado.erro || 'Algo deu errado. Tente novamente.');
    erro.status = resposta.status;
    throw erro;
  }
  return resultado;
}

const _hora = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: FUSO });
const _horaSeg = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: FUSO });
const _dataCurta = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', timeZone: FUSO });
const _dataLonga = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', day: 'numeric', month: 'long', timeZone: FUSO });
const _iso = new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone: FUSO });

const fmt = {
  hora: iso => iso ? _hora.format(new Date(iso)) : '—',
  horaSeg: iso => iso ? _horaSeg.format(new Date(iso)) : '—',
  dataCurta: iso => iso ? _dataCurta.format(new Date(iso)) : '—',
  // data AAAA-MM-DD → "quarta-feira, 25 de novembro"
  dataLonga: dia => _dataLonga.format(new Date(dia + 'T12:00:00-03:00')),
  diaMes: dia => dia.slice(8, 10) + '/' + dia.slice(5, 7),
  minutos: m => {
    if (m === null || m === undefined) return '—';
    m = Math.round(m);
    return m < 60 ? `${m} min` : `${Math.floor(m / 60)}h${String(m % 60).padStart(2, '0')}`;
  },
  numero: (n, casas = 0) => n === null || n === undefined ? '—'
    : n.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas }),
  pct: n => n === null || n === undefined ? '—' : `${n}%`,
};

// Data de hoje no fuso de São Paulo (AAAA-MM-DD).
function hojeISO() {
  const p = Object.fromEntries(_iso.formatToParts(new Date()).map(x => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}`;
}
function somarDias(dia, n) {
  const d = new Date(dia + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

// Aceita "BOV-ABCD", "bov abcd" ou "ABCD"; devolve "BOV-ABCD" ou null.
function normalizarCodigo(texto) {
  let limpo = String(texto || '').toUpperCase().replace(/[^0-9A-Z]/g, '');
  if (limpo.startsWith('BOV')) limpo = limpo.slice(3);
  return /^[2-9A-HJ-NP-Z]{4}$/.test(limpo) ? 'BOV-' + limpo : null;
}

function esc(texto) {
  return String(texto ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

let _avisoTimer;
function avisar(mensagem, tipo = '') {
  let el = document.querySelector('.aviso-flutuante');
  if (!el) {
    el = document.createElement('div');
    el.setAttribute('role', 'status');
    document.body.append(el);
  }
  el.className = 'aviso-flutuante ' + tipo;
  el.textContent = mensagem;
  el.hidden = false;
  clearTimeout(_avisoTimer);
  _avisoTimer = setTimeout(() => { el.hidden = true; }, 3500);
}

// QR code (SVG) do código da visita. Usa vendor/qrcode.js.
function qrSvg(texto, rotulo = 'QR code do código da visita') {
  if (typeof qrcode === 'undefined') return '';
  const qr = qrcode(0, 'M');
  qr.addData(texto);
  qr.make();
  return qr.createSvgTag({ cellSize: 6, margin: 2, scalable: true, title: rotulo });
}

// Usuário logado (telas da equipe).
async function usuarioAtual() {
  try { return await api('/api/eu'); } catch { return null; }
}
async function sair() {
  try { await api('/api/logout', { dados: {} }); } finally { location.href = '/login'; }
}

// Menu lateral das telas da equipe.
async function montarLateral(ativo) {
  const itens = [
    ['/dashboard', '📊', 'Dashboard'],
    ['/cardapio', '🍽️', 'Cardápio do dia'],
    ['/terminal', '🖥️', 'Terminal'],
  ];
  const nav = document.querySelector('.lateral');
  nav.innerHTML = `<span class="logo"><img src="/img/logo.png" alt="Bovinu's Grill & Beer"></span>` +
    itens.map(([href, icone, nome]) =>
      `<a href="${href}" class="${href === ativo ? 'ativo' : ''}"><span aria-hidden="true">${icone}</span>${nome}</a>`
    ).join('') +
    `<div class="rodape"><div id="usuario-logado"></div>
      <button type="button" class="btn btn-fantasma" id="btn-sair" style="color:#fff;padding:.3rem 0;min-height:0">⎋ Sair</button>
      <div style="margin-top:.6rem">Bovinu's Connect · Unidade Augusta<br>MVP Hackathon FMU</div></div>`;
  document.getElementById('btn-sair').onclick = sair;
  const u = await usuarioAtual();
  if (u) document.getElementById('usuario-logado').textContent = `${u.nome} · ${u.papel}`;
}
