import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import {
  motion, AnimatePresence, MotionConfig, LayoutGroup,
  useScroll, useSpring, useTransform, useInView, animate,
} from 'motion/react';
import {
  REPO, DOCS, EQUIPE, NAV, FATOS, DORES, JORNADAS, TELAS, INDICADORES, GANHOS, TECNOLOGIAS, DOCUMENTOS,
} from './dados.js';

const B = import.meta.env.BASE_URL;
const tela = id => `${B}telas/${id}.webp`;
const raiz = caminho => `${B}../${caminho}`; // arquivos fora de site/ (docs, slides, vídeo)
const TELA = Object.fromEntries(TELAS.map(t => [t.id, t]));
const surgir = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-80px' },
  transition: { duration: .6, ease: [.22, 1, .36, 1] },
};

// ---------------------------------------------------------------- utilidades
function Marca() {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true">
      <defs>
        <linearGradient id="gm" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f2b552" /><stop offset=".55" stopColor="#e0523a" /><stop offset="1" stopColor="#a3242c" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#gm)" />
      <path d="M9 21.5c2.2-6.5 11.8-6.5 14 0" stroke="#1b0d0b" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      <circle cx="16" cy="11.5" r="2.6" fill="#1b0d0b" />
      <path d="M8 24h16" stroke="#1b0d0b" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

function Moldura({ id, prioridade, className = '' }) {
  const t = TELA[id];
  const img = <img src={tela(id)} alt={`${t.titulo}: ${t.desc}`} loading={prioridade ? 'eager' : 'lazy'} />;
  if (t.tipo === 'celular') return <div className={`moldura-celular ${className}`}>{img}</div>;
  if (t.tipo === 'tv') return <div className={`moldura-tv ${className}`}>{img}</div>;
  if (t.tipo === 'papel') return <div className={`moldura-papel ${className}`}>{img}</div>;
  return <div className={`moldura-desktop ${className}`}><div className="barra"><i /><i /><i /></div>{img}</div>;
}

function Contador({ valor }) {
  const ref = useRef(null);
  const visto = useInView(ref, { once: true });
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!visto) return;
    const c = animate(0, Number(valor), { duration: 1.4, ease: 'easeOut', onUpdate: v => setN(Math.round(v)) });
    return () => c.stop();
  }, [visto, valor]);
  return <strong ref={ref}>{n}</strong>;
}

function CabSecao({ sobre, titulo, children }) {
  return (
    <motion.div className="cab-secao" {...surgir}>
      <span className="sobretitulo">{sobre}</span>
      <h2>{titulo}</h2>
      {children && <p className="lead">{children}</p>}
    </motion.div>
  );
}

// ---------------------------------------------------------------- navegação
function Nav() {
  const [rolou, setRolou] = useState(false);
  const [ativa, setAtiva] = useState('');
  const [aberto, setAberto] = useState(false);
  const { scrollYProgress } = useScroll();
  const escala = useSpring(scrollYProgress, { stiffness: 120, damping: 30 });

  useEffect(() => {
    const aoRolar = () => setRolou(window.scrollY > 20);
    aoRolar();
    window.addEventListener('scroll', aoRolar, { passive: true });
    const obs = new IntersectionObserver(
      es => es.forEach(e => e.isIntersecting && setAtiva(e.target.id)),
      { rootMargin: '-45% 0px -50% 0px' },
    );
    ['topo', ...NAV.map(([id]) => id)].forEach(id => { const el = document.getElementById(id); if (el) obs.observe(el); });
    return () => { window.removeEventListener('scroll', aoRolar); obs.disconnect(); };
  }, []);

  return (
    <header className={`nav ${rolou || aberto ? 'rolou' : ''}`}>
      <nav className="container nav-in" aria-label="Seções">
        <a href="#topo" className="marca" onClick={() => setAberto(false)}><Marca /> Bovinu's Connect</a>
        <LayoutGroup>
          <ul className={`nav-links ${aberto ? 'aberto' : ''}`}>
            {NAV.map(([id, rotulo]) => (
              <li key={id}>
                <a href={`#${id}`} className={ativa === id ? 'ativo' : ''} onClick={() => setAberto(false)}
                  aria-current={ativa === id ? 'true' : undefined}>
                  {ativa === id && <motion.span layoutId="nav-pill" className="nav-pill" transition={{ type: 'spring', stiffness: 380, damping: 32 }} />}
                  {rotulo}
                </a>
              </li>
            ))}
          </ul>
        </LayoutGroup>
        <a className="btn nav-github" href={REPO} target="_blank" rel="noreferrer">GitHub ↗</a>
        <button className="nav-menu" aria-label={aberto ? 'Fechar menu' : 'Abrir menu'} aria-expanded={aberto} onClick={() => setAberto(a => !a)}>
          {aberto ? '✕' : '☰'}
        </button>
      </nav>
      <motion.div className="progresso" style={{ scaleX: escala }} />
    </header>
  );
}

// ---------------------------------------------------------------- hero
function Hero() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] });
  const yDesk = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const yCel = useTransform(scrollYProgress, [0, 1], [0, -60]);
  return (
    <section className="hero" id="topo" ref={ref}>
      <div className="hero-fundo" aria-hidden="true">
        <div className="grade-fundo" />
        <motion.div className="brilho brilho-1" animate={{ scale: [1, 1.12, 1] }} transition={{ duration: 9, repeat: Infinity }} />
        <div className="brilho brilho-2" />
      </div>
      <div className="container">
        <div className="hero-grid">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .8, ease: [.22, 1, .36, 1] }}>
            <span className="sobretitulo">Hackathon FMU 2026.2 · Bovinu's Grill &amp; Beer</span>
            <h1>A jornada do almoço, <span className="grad-texto">do aviso à avaliação.</span></h1>
            <p className="lead">
              O cliente avisa que vem e o que quer encontrar no buffet. A equipe registra chegada, balança e saída com um
              código. A gestão vê, ao vivo, o que antes ninguém media.
            </p>
            <div className="hero-acoes">
              <a className="btn btn-primario" href="#jornada">Ver a jornada →</a>
              <a className="btn" href="#midia">▶ Assistir ao vídeo</a>
              <a className="btn" href={REPO} target="_blank" rel="noreferrer">Código no GitHub</a>
            </div>
            <div className="hero-selos">
              <span className="selo selo-real"><i />MVP funcional</span>
              <span className="selo selo-sim"><i />Telas com dados simulados</span>
              <span className="selo"><i />Projeto acadêmico</span>
            </div>
          </motion.div>

          <div className="hero-visual" aria-hidden="true">
            <motion.div style={{ y: yDesk }} initial={{ opacity: 0, x: 60 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 1, delay: .15, ease: [.22, 1, .36, 1] }}>
              <Moldura id="20-dashboard-hoje" prioridade className="moldura-desktop" />
            </motion.div>
            <motion.div className="moldura-celular" style={{ y: yCel, position: 'absolute', right: '-4%', bottom: -10, width: '36%' }}
              initial={{ opacity: 0, y: 80 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: .35, ease: [.22, 1, .36, 1] }}>
              <img src={tela('03-cliente-codigo')} alt="" />
            </motion.div>
            <motion.div className="flutua-tag tag-1" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: [0, -8, 0] }}
              transition={{ opacity: { delay: .8 }, y: { duration: 5, repeat: Infinity, ease: 'easeInOut' } }}>
              <span className="ponto-vivo" />
              <div><strong>BOV-YXZN</strong><small>check-in registrado</small></div>
            </motion.div>
            <motion.div className="flutua-tag tag-2" initial={{ opacity: 0 }} animate={{ opacity: 1, y: [0, 8, 0] }}
              transition={{ opacity: { delay: 1 }, y: { duration: 6, repeat: Infinity, ease: 'easeInOut' } }}>
              🧽<div><strong>Mesa 12</strong><small>aguardando limpeza · há 3 min</small></div>
            </motion.div>
          </div>
        </div>

        <motion.div className="fatos" {...surgir}>
          {FATOS.map(([n, t]) => <div className="fato" key={t}><Contador valor={n} /><span>{t}</span></div>)}
        </motion.div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- problema
function Problema() {
  const mover = e => {
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty('--mx', `${e.clientX - r.left}px`);
    e.currentTarget.style.setProperty('--my', `${e.clientY - r.top}px`);
  };
  return (
    <section id="problema">
      <div className="container">
        <CabSecao sobre="O problema" titulo="Quatro dores que hoje não aparecem em nenhum número.">
          No almoço por quilo da Unidade Augusta, saber quanto se vendeu não diz quem vem, quando chega, quanto espera,
          o que queria encontrar no buffet nem como saiu.
        </CabSecao>
        <div className="dores">
          {DORES.map((d, i) => (
            <motion.article className="dor" key={d.n} onMouseMove={mover} {...surgir} transition={{ ...surgir.transition, delay: i * .08 }}>
              <span className="dor-num">{d.n}</span>
              <h3>{d.titulo}</h3>
              <p>{d.dor}</p>
              <div className="resposta"><strong>Como o Connect responde</strong><p>{d.resposta}</p></div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- jornada
const DURACAO_PASSO = 5200;
function Jornada() {
  const [tipo, setTipo] = useState('planejado');
  const [i, setI] = useState(0);
  const [auto, setAuto] = useState(true);
  const [pausa, setPausa] = useState(false);
  const ref = useRef(null);
  const visivel = useInView(ref, { margin: '-30%' });
  const passos = JORNADAS[tipo].passos;
  const rodando = auto && !pausa && visivel;

  useEffect(() => { setI(0); }, [tipo]);
  useEffect(() => {
    if (!rodando) return;
    const t = setTimeout(() => setI(x => (x + 1) % passos.length), DURACAO_PASSO);
    return () => clearTimeout(t);
  }, [rodando, i, passos.length]);

  const p = passos[i];
  return (
    <section id="jornada" ref={ref}>
      <div className="container">
        <CabSecao sobre="A jornada" titulo="Duas portas de entrada, um mesmo código do começo ao fim.">
          Quem planeja pelo app e quem chega sem avisar seguem o mesmo fluxo depois do check-in. Clique nos passos ou deixe
          a jornada avançar sozinha.
        </CabSecao>

        <div className="abas" role="tablist" aria-label="Tipo de cliente">
          {Object.entries(JORNADAS).map(([k, j]) => (
            <button key={k} role="tab" className="aba" aria-selected={tipo === k} onClick={() => setTipo(k)}>
              {tipo === k && <motion.span layoutId="aba-pill" className="aba-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
              {j.rotulo}
            </button>
          ))}
        </div>

        <div className="jornada" onMouseEnter={() => setPausa(true)} onMouseLeave={() => setPausa(false)}>
          <div>
            <ol className="passos">
              {passos.map((s, k) => (
                <li key={tipo + k}>
                  <button className={`passo ${k === i ? 'ativo' : ''}`} onClick={() => setI(k)} aria-current={k === i ? 'step' : undefined}>
                    <span className="passo-n">{k + 1}</span>
                    <span>
                      <strong>{s.titulo}</strong>
                      <span>{s.texto}</span>
                      <small>{s.onde}</small>
                    </span>
                    {k === i && rodando && (
                      <motion.span className="passo-barra" key={`${tipo}-${i}`} initial={{ scaleX: 0 }} animate={{ scaleX: 1 }}
                        transition={{ duration: DURACAO_PASSO / 1000, ease: 'linear' }} style={{ width: '100%' }} />
                    )}
                  </button>
                </li>
              ))}
            </ol>
            <div className="controles-auto">
              <button onClick={() => setAuto(a => !a)} aria-pressed={auto}>{auto ? '❚❚ Pausar' : '▶ Reproduzir'}</button>
              <span>Passo {i + 1} de {passos.length}</span>
            </div>
          </div>

          <div className="palco" aria-live="polite">
            <AnimatePresence mode="wait">
              <motion.div key={tipo + p.tela}
                initial={{ opacity: 0, y: 24, scale: .97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -16, scale: .98 }} transition={{ duration: .45, ease: [.22, 1, .36, 1] }}>
                <Moldura id={p.tela} />
                <p className="palco-legenda">{TELA[p.tela].titulo} · {p.onde}</p>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- telas
const GRUPOS = ['Todas', 'Cliente', 'Totem', 'Gestão', 'TVs'];
function Telas() {
  const [grupo, setGrupo] = useState('Todas');
  const [aberta, setAberta] = useState(null);
  const lista = useMemo(() => TELAS.filter(t => grupo === 'Todas' || t.grupo === grupo), [grupo]);

  const mover = useCallback(d => setAberta(a => (a + d + lista.length) % lista.length), [lista.length]);
  useEffect(() => {
    if (aberta === null) return;
    const tecla = e => {
      if (e.key === 'Escape') setAberta(null);
      if (e.key === 'ArrowRight') mover(1);
      if (e.key === 'ArrowLeft') mover(-1);
    };
    document.addEventListener('keydown', tecla);
    document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', tecla); document.body.style.overflow = ''; };
  }, [aberta, mover]);

  const atual = aberta !== null ? lista[aberta] : null;
  return (
    <section id="telas">
      <div className="container">
        <CabSecao sobre="Demonstração visual" titulo="As telas do MVP, capturadas da aplicação rodando.">
          Cada imagem saiu do sistema em funcionamento, com o banco de demonstração. Filtre por quem usa e clique para ampliar.
        </CabSecao>
        <LayoutGroup>
          <div className="filtros" role="group" aria-label="Filtrar telas">
            {GRUPOS.map(g => (
              <button key={g} className="filtro" aria-pressed={grupo === g} onClick={() => setGrupo(g)}>
                {grupo === g && <motion.span layoutId="filtro-pill" className="filtro-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
                {g}
              </button>
            ))}
          </div>
          <motion.div className="galeria" layout>
            <AnimatePresence mode="popLayout">
              {lista.map((t, k) => (
                <motion.button layout key={t.id} className="cartao-tela" onClick={() => setAberta(k)}
                  initial={{ opacity: 0, scale: .94 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: .94 }}
                  transition={{ duration: .35 }}>
                  <div className={`miniatura ${t.tipo}`}><img src={tela(t.id)} alt="" loading="lazy" style={t.zoom ? { '--z': t.zoom, objectPosition: t.foco } : undefined} /></div>
                  <div className="info"><span>{t.grupo}</span><strong>{t.titulo}</strong><p>{t.desc}</p></div>
                </motion.button>
              ))}
            </AnimatePresence>
          </motion.div>
        </LayoutGroup>
        <p className="aviso-dados">
          <span className="selo selo-sim"><i />Dados simulados</span>
          Números e nomes nas telas vêm do gerador de demonstração (<code>seed.py</code>), não de clientes reais.
        </p>
      </div>

      <AnimatePresence>
        {atual && (
          <motion.div className="lightbox" role="dialog" aria-modal="true" aria-label={atual.titulo}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setAberta(null)}>
            <motion.figure key={atual.id} initial={{ opacity: 0, scale: .96 }} animate={{ opacity: 1, scale: 1 }} onClick={e => e.stopPropagation()}>
              <img src={tela(atual.id)} alt={`${atual.titulo}: ${atual.desc}`} />
              <figcaption><strong>{atual.titulo}</strong> · {atual.desc} <br /><small>{aberta + 1} de {lista.length} · ← → para navegar · Esc fecha</small></figcaption>
            </motion.figure>
            <button className="lb-btn lb-fechar" aria-label="Fechar" onClick={() => setAberta(null)}>✕</button>
            <button className="lb-btn lb-ant" aria-label="Anterior" onClick={e => { e.stopPropagation(); mover(-1); }}>←</button>
            <button className="lb-btn lb-prox" aria-label="Próxima" onClick={e => { e.stopPropagation(); mover(1); }}>→</button>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

// ---------------------------------------------------------------- indicadores
function SimuladorVisita() {
  const [etapa, setEtapa] = useState(0); // 0 aguardando, 1 check-in, 2 buffet, 3 check-out, 4 avaliada
  const [visitas, setVisitas] = useState(2);
  const [pontos, setPontos] = useState(1);
  const [msg, setMsg] = useState('');
  const acao = (nova, texto) => { setEtapa(nova); setMsg(texto); };
  return (
    <motion.div className="painel" {...surgir}>
      <span className="selo"><i />Simulação no navegador</span>
      <h3>Experimente: uma visita do começo ao fim</h3>
      <p>Mesmas regras do app: a visita conta no check-out e a avaliação vale 1 ponto. Nada é enviado a servidor.</p>
      <div className="sim-etapas">
        {[['Check-in', 1], ['Buffet', 2], ['Check-out', 3]].map(([n, e]) => (
          <motion.div key={n} className={`sim-etapa ${etapa >= e ? 'feito' : ''}`} animate={etapa === e ? { scale: [1, 1.05, 1] } : {}}>
            <b>{n}</b>{etapa >= e ? '✓ registrado' : e === 2 ? 'opcional' : 'pendente'}
          </motion.div>
        ))}
      </div>
      <div className="sim-acoes">
        <button className="btn" disabled={etapa !== 0} onClick={() => acao(1, 'Entrada registrada no totem.')}>Check-in</button>
        <button className="btn" disabled={etapa !== 1} onClick={() => acao(2, 'Buffet concluído na balança.')}>Balança</button>
        <button className="btn" disabled={etapa < 1 || etapa > 2} onClick={() => { acao(3, 'Saída no caixa: +1 visita.'); setVisitas(v => v + 1); }}>Check-out</button>
        <button className="btn btn-primario" disabled={etapa !== 3} onClick={() => { acao(4, 'Avaliação enviada: +1 ponto.'); setPontos(p => p + 1); }}>Avaliar</button>
        <button className="btn" onClick={() => { setEtapa(0); setMsg(''); }}>Nova visita</button>
      </div>
      <div className="sim-fid">
        <div><motion.strong key={visitas} initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>{visitas}</motion.strong><span>Você já veio {visitas} {visitas === 1 ? 'vez' : 'vezes'}</span></div>
        <div><motion.strong key={pontos} initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>{pontos}</motion.strong><span>Você tem {pontos} {pontos === 1 ? 'ponto' : 'pontos'}</span></div>
      </div>
      <p className="sim-msg" aria-live="polite">{msg}</p>
    </motion.div>
  );
}

const MESAS = [[4, 2], [12, 9], [27, 21], [7, 33], [59, 41]]; // [mesa, minutos desde o check-out no instante 0]
function JanelaLimpeza() {
  const [passou, setPassou] = useState(0);
  const visiveis = MESAS.map(([m, idade]) => [m, idade + passou]).filter(([, idade]) => idade < 45).sort((a, b) => b[1] - a[1]);
  return (
    <motion.div className="painel" {...surgir} transition={{ ...surgir.transition, delay: .1 }}>
      <span className="selo"><i />Simulação no navegador</span>
      <h3>Experimente: a janela de 45 minutos da TV Salão</h3>
      <p>Arraste para avançar o relógio. Cada mesa sai da lista sozinha 45 min depois do check-out (<code>JANELA_LIMPEZA_MIN</code>).</p>
      <input className="slider" type="range" min="0" max="45" value={passou} onChange={e => setPassou(Number(e.target.value))} aria-label="Minutos que passaram" />
      <div className="slider-rot"><span>agora</span><span>+{passou} min</span><span>+45 min</span></div>
      <ul className="mesas">
        <AnimatePresence initial={false}>
          {visiveis.map(([m, idade]) => (
            <motion.li key={m} layout initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 30 }}>
              <span>Mesa {m}</span><span>há {idade} min</span>
            </motion.li>
          ))}
          {visiveis.length === 0 && <motion.li key="vazia" className="vazia" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>Nenhuma mesa aguardando limpeza</motion.li>}
        </AnimatePresence>
      </ul>
    </motion.div>
  );
}

function Indicadores() {
  const [aberto, setAberto] = useState(null);
  return (
    <section id="indicadores">
      <div className="container">
        <CabSecao sobre="Inteligência gerencial" titulo="Indicadores de jornada que vão além do ticket médio.">
          Cada indicador nasce de um registro simples: um horário no totem, na balança ou no caixa, uma intenção ou uma
          avaliação. Clique para ver a fórmula usada no código.
        </CabSecao>
        <div className="ind-grade">
          {INDICADORES.map((d, k) => (
            <motion.button key={d.nome} className="ind" aria-expanded={aberto === k} onClick={() => setAberto(aberto === k ? null : k)}
              {...surgir} transition={{ ...surgir.transition, delay: (k % 4) * .06 }}>
              <strong>{d.nome}</strong>
              <p>{d.uso}</p>
              <AnimatePresence initial={false}>
                {aberto === k && (
                  <motion.code initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                    {d.formula}
                  </motion.code>
                )}
              </AnimatePresence>
              <span className="mais">{aberto === k ? 'Ocultar fórmula' : 'Ver fórmula +'}</span>
            </motion.button>
          ))}
        </div>

        <div className="experimente">
          <SimuladorVisita />
          <JanelaLimpeza />
        </div>

        <div className="ganhos">
          {GANHOS.map((g, k) => (
            <motion.div className="ganho" key={g.eixo} {...surgir} transition={{ ...surgir.transition, delay: k * .08 }}>
              <div className="ganho-cab"><h3><span aria-hidden="true">{g.icone}</span>{g.eixo}</h3><span className="selo selo-hip"><i />Hipótese</span></div>
              <ul>{g.itens.map(t => <li key={t}>{t}</li>)}</ul>
            </motion.div>
          ))}
        </div>

        <motion.div className="transparencia" {...surgir}>
          <div><span className="selo selo-real"><i />Implementado</span>
            <p>Telas, regras e indicadores descritos aqui funcionam no MVP e são cobertos por 21 testes automatizados.</p></div>
          <div><span className="selo selo-sim"><i />Simulado</span>
            <p>Todos os números das capturas vêm de dados gerados pelo <code>seed.py</code>. Não são resultados da Bovinu's.</p></div>
          <div><span className="selo selo-hip"><i />Hipótese</span>
            <p>Os ganhos de eficiência, financeiros e de gestão são expectativas a validar em operação real — ainda não medidos.</p></div>
        </motion.div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- arquitetura
const COMANDOS = `git clone ${REPO}.git
cd bovinus-connect
python seed.py      # banco de demonstração (dados simulados)
python app.py       # http://127.0.0.1:8000
python testes.py    # 21 testes`;
function Arquitetura({ abrirImagem }) {
  const [copiado, setCopiado] = useState(false);
  const copiar = async () => {
    try { await navigator.clipboard.writeText(COMANDOS.replace(/ +#.*$/gm, '')); setCopiado(true); setTimeout(() => setCopiado(false), 1800); } catch { /* sem permissão */ }
  };
  return (
    <section id="arquitetura">
      <div className="container">
        <CabSecao sobre="Arquitetura e tecnologias" titulo="Simples de propósito: um processo, um banco, qualquer navegador.">
          Sem frameworks, sem nuvem e sem serviços pagos no app. Roda num notebook da casa e atende celulares, totem, caixa e TVs pela rede local.
        </CabSecao>
        <div className="arq">
          <motion.div {...surgir}>
            <button className="diagrama" onClick={() => abrirImagem(`${B}diagramas/arquitetura.svg`, 'Arquitetura do Bovinu\'s Connect')}>
              <img src={`${B}diagramas/arquitetura.svg`} alt="Diagrama: celulares, totem, balança, caixa, notebook e TVs acessam o app.py por HTTP, que grava no SQLite." />
            </button>
            <div className="aviso-estatico">
              <strong>Este site é uma demonstração estática.</strong> Ele mostra o projeto com capturas e simulações no navegador.
              O sistema de verdade é o backend Python (<code>app.py</code>), que roda separadamente na máquina da equipe.
            </div>
          </motion.div>
          <motion.div {...surgir} transition={{ ...surgir.transition, delay: .1 }}>
            <div className="techs">
              {TECNOLOGIAS.map(([n, d]) => <div className="tech" key={n}><strong>{n}</strong><span>{d}</span></div>)}
            </div>
            <div className="terminal-bloco">
              <div className="topo"><span>Rodar localmente (Python 3.10+)</span>
                <button className="copiar" onClick={copiar}>{copiado ? 'Copiado ✓' : 'Copiar'}</button></div>
              <pre>{COMANDOS.split('\n').map((l, k) => {
                const [cmd, coment] = l.split(/(?= +#)/);
                return <div key={k}>{cmd}{coment && <span>{coment}</span>}</div>;
              })}</pre>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- documentação
function Documentacao({ abrirImagem }) {
  return (
    <section id="documentacao">
      <div className="container">
        <CabSecao sobre="Documentação técnica" titulo="Requisitos, jornada, DER e dicionário de dados.">
          Os documentos estão no repositório em Markdown e em PDF. O dicionário de dados foi conferido com o <code>schema.sql</code>.
        </CabSecao>
        <div className="docs">
          {DOCUMENTOS.map((d, k) => (
            <motion.article className="doc" key={d.md} {...surgir} transition={{ ...surgir.transition, delay: k * .06 }}>
              <span className="ic" aria-hidden="true">📄</span>
              <h3>{d.titulo}</h3>
              <p>{d.desc}</p>
              <div className="doc-links">
                <a href={DOCS + d.md} target="_blank" rel="noreferrer">Ler no GitHub</a>
                <a href={raiz('docs/pdf/' + d.pdf)} target="_blank" rel="noreferrer">PDF</a>
              </div>
            </motion.article>
          ))}
        </div>
        <div className="diagramas">
          {[['jornada', 'Jornada: planejado e espontâneo convergem no check-in'], ['der', 'DER: entidades do schema.sql e as views jornada e fidelidade']].map(([n, leg]) => (
            <motion.figure key={n} {...surgir}>
              <button className="diagrama" onClick={() => abrirImagem(`${B}diagramas/${n}.svg`, leg)}>
                <img src={`${B}diagramas/${n}.svg`} alt={leg} loading="lazy" />
              </button>
              <figcaption>{leg}</figcaption>
            </motion.figure>
          ))}
        </div>
        <div className="extras">
          <a className="btn" href={REPO + '#readme'} target="_blank" rel="noreferrer">README do projeto</a>
          <a className="btn" href={DOCS + 'ESPECIFICACAO.md'} target="_blank" rel="noreferrer">Especificação completa</a>
          <a className="btn" href={REPO + '/blob/main/schema.sql'} target="_blank" rel="noreferrer">schema.sql</a>
          <a className="btn" href={REPO + '/blob/main/testes.py'} target="_blank" rel="noreferrer">testes.py</a>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- mídia e equipe
function Midia() {
  const iniciais = n => n.split(' ').map(p => p[0]).slice(0, 2).join('');
  return (
    <section id="midia">
      <div className="container">
        <CabSecao sobre="Vídeo, apresentação e equipe" titulo="Veja o Connect em menos de dois minutos.">
          Vídeo em motion design com as telas reais do MVP e a apresentação usada na banca.
        </CabSecao>
        <div className="midia">
          <motion.div className="video-box" {...surgir}>
            <video controls preload="none" poster={raiz('video/capa.jpg')}>
              <source src={raiz('video/bovinus-connect.mp4')} type="video/mp4" />
              Seu navegador não reproduz vídeo. <a href={raiz('video/bovinus-connect.mp4')}>Baixe o MP4</a>.
            </video>
          </motion.div>
          <motion.div className="slides-box" {...surgir} transition={{ ...surgir.transition, delay: .1 }}>
            <img src={raiz('slides/capa.png')} alt="Capa da apresentação Bovinu's Connect" loading="lazy" />
            <h3>Apresentação</h3>
            <p className="lead" style={{ fontSize: '.95rem' }}>Problema, solução, jornada, indicadores, arquitetura e próximos passos.</p>
            <div className="btns">
              <a className="btn btn-primario" href={raiz('slides/bovinus-connect.pdf')} target="_blank" rel="noreferrer">Abrir PDF</a>
              <a className="btn" href={raiz('slides/bovinus-connect.pptx')} download>Baixar PPTX</a>
            </div>
          </motion.div>
        </div>
        <div className="equipe">
          {EQUIPE.map((n, k) => (
            <motion.div className="membro" key={n} {...surgir} transition={{ ...surgir.transition, delay: k * .08 }}>
              <span className="avatar" aria-hidden="true">{iniciais(n)}</span>
              <div><strong>{n}</strong><span>Equipe Bovinu's Connect · FMU</span></div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- app
export default function App() {
  const [imagem, setImagem] = useState(null);
  const abrirImagem = (src, legenda) => setImagem({ src, legenda });
  useEffect(() => {
    if (!imagem) return;
    const tecla = e => e.key === 'Escape' && setImagem(null);
    document.addEventListener('keydown', tecla);
    return () => document.removeEventListener('keydown', tecla);
  }, [imagem]);

  return (
    <MotionConfig reducedMotion="user">
      <a href="#problema" className="sr">Pular para o conteúdo</a>
      <Nav />
      <main>
        <Hero />
        <Problema />
        <Jornada />
        <Telas />
        <Indicadores />
        <Arquitetura abrirImagem={abrirImagem} />
        <Documentacao abrirImagem={abrirImagem} />
        <Midia />
      </main>
      <footer className="rodape">
        <div className="container rodape-grid">
          <div>
            <a href="#topo" className="marca"><Marca /> Bovinu's Connect</a>
            <p>Projeto acadêmico do Hackathon FMU 2026.2, desenvolvido por {EQUIPE.join(', ')}. Não é o site oficial da
              Bovinu's Grill &amp; Beer. Dados das telas são simulados.</p>
          </div>
          <div>
            <p><a href={REPO} target="_blank" rel="noreferrer">Repositório no GitHub</a></p>
            <p>Trilha do vídeo: Pixabay (licença de conteúdo Pixabay).</p>
          </div>
        </div>
      </footer>

      <AnimatePresence>
        {imagem && (
          <motion.div className="lightbox" role="dialog" aria-modal="true" aria-label={imagem.legenda}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setImagem(null)}>
            <figure>
              <img src={imagem.src} alt={imagem.legenda} style={{ background: '#fffdf9', width: 'min(1200px, 100%)', maxHeight: 'calc(100vh - 150px)', objectFit: 'contain' }} />
              <figcaption>{imagem.legenda}</figcaption>
            </figure>
            <button className="lb-btn lb-fechar" aria-label="Fechar" onClick={() => setImagem(null)}>✕</button>
          </motion.div>
        )}
      </AnimatePresence>
    </MotionConfig>
  );
}
