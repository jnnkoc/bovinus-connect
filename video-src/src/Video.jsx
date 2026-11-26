import { AbsoluteFill, Audio, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { TransitionSeries, linearTiming, springTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { slide } from '@remotion/transitions/slide';
import { wipe } from '@remotion/transitions/wipe';
import {
  COR, GRAD, TITULO, FONTE, tela, useEntrada, useSaida, Fundo, Palavras, Sobretitulo, Legenda, Celular,
  Navegador, Destaque, trilha, Chip,
} from './componentes.jsx';

const T = 18; // duração das transições (quadros)

function Marca({ tamanho = 120 }) {
  return (
    <svg viewBox="0 0 32 32" width={tamanho} height={tamanho}>
      <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#f2b552" /><stop offset=".55" stopColor="#e0523a" /><stop offset="1" stopColor="#a3242c" /></linearGradient></defs>
      <rect width="32" height="32" rx="9" fill="url(#g)" />
      <path d="M9 21.5c2.2-6.5 11.8-6.5 14 0" stroke="#1b0d0b" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      <circle cx="16" cy="11.5" r="2.6" fill="#1b0d0b" />
      <path d="M8 24h16" stroke="#1b0d0b" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

const Palco = ({ children, tom }) => (
  <AbsoluteFill><Fundo tom={tom} /><AbsoluteFill style={{ padding: '0 120px', justifyContent: 'center' }}>{children}</AbsoluteFill></AbsoluteFill>
);

// 1 · abertura
function Abertura() {
  const f = useCurrentFrame();
  const s = useEntrada(4, { damping: 12, stiffness: 90 });
  const sub = useEntrada(40);
  return (
    <AbsoluteFill><Fundo />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 36, textAlign: 'center' }}>
        <div style={{ transform: `scale(${s}) rotate(${(1 - s) * -20}deg)` }}><Marca tamanho={150} /></div>
        <div style={{ fontFamily: TITULO, fontWeight: 700, fontSize: 124, color: COR.texto, letterSpacing: -4 }}>
          <Palavras texto="Bovinu's Connect" atraso={14} passo={6} />
        </div>
        <div style={{ fontFamily: TITULO, fontSize: 50, color: COR.texto2, opacity: sub, transform: `translateY(${(1 - sub) * 24}px)` }}>
          A jornada do almoço, <span style={{ background: GRAD, WebkitBackgroundClip: 'text', color: 'transparent' }}>do aviso à avaliação.</span>
        </div>
        <div style={{ opacity: interpolate(f, [70, 90], [0, 1], { extrapolateRight: 'clamp', extrapolateLeft: 'clamp' }), fontFamily: FONTE, fontSize: 26, color: COR.texto3, letterSpacing: 4, textTransform: 'uppercase' }}>
          Hackathon FMU 2026.2 · Bovinu's Grill &amp; Beer · Unidade Augusta
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}

// 2 · problema: perguntas que ninguém mede
function Problema() {
  const f = useCurrentFrame();
  const perguntas = ['Quem vem hoje?', 'Quando chega?', 'Quanto espera?', 'O que queria no buffet?', 'Como saiu?'];
  const fim = useEntrada(200);
  return (
    <Palco>
      <div style={{ width: '100%' }}>
        <Sobretitulo atraso={4}>O problema</Sobretitulo>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 22, marginTop: 50, maxWidth: 1500 }}>
          {perguntas.map((p, i) => {
            const s = useEntrada(16 + i * 22, { damping: 15 });
            const apagar = interpolate(f, [190, 215], [1, .35], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
            return (
              <div key={p} style={{
                fontFamily: TITULO, fontSize: 70, fontWeight: 700, color: COR.texto, padding: '20px 40px', borderRadius: 30,
                border: `2px solid ${COR.linha}`, background: 'rgba(255,255,255,.04)', opacity: s * apagar,
                transform: `translateY(${(1 - s) * 60}px) scale(${0.9 + s * 0.1})`,
              }}>{p}</div>
            );
          })}
        </div>
        <div style={{ marginTop: 70, fontFamily: TITULO, fontSize: 84, fontWeight: 700, opacity: fim, transform: `translateY(${(1 - fim) * 30}px)`, color: COR.texto }}>
          Hoje, <span style={{ background: GRAD, WebkitBackgroundClip: 'text', color: 'transparent' }}>nada disso é medido.</span>
        </div>
      </div>
    </Palco>
  );
}

// 3 · solução: três pontas
function Solucao() {
  const pontas = [['📱', 'App do cliente', 'planeja · acompanha · avalia'], ['🖥️', 'Terminal da equipe', 'entrada · balança · caixa'], ['📊', 'Gestão', 'dashboard · TVs · cardápio']];
  return (
    <Palco>
      <div style={{ width: '100%' }}>
        <Sobretitulo atraso={2}>A solução</Sobretitulo>
        <div style={{ fontFamily: TITULO, fontSize: 92, fontWeight: 700, color: COR.texto, margin: '26px 0 70px', letterSpacing: -2 }}>
          <Palavras texto="Uma plataforma. Três pontas. Um só código." atraso={8} destaque={[5, 6, 7]} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 34 }}>
          {pontas.map(([ic, t, d], i) => {
            const s = useEntrada(40 + i * 12, { damping: 16 });
            return (
              <div key={t} style={{
                borderRadius: 32, padding: 44, background: COR.bg2, border: `1px solid ${COR.linha}`, opacity: s,
                transform: `translateY(${(1 - s) * 80}px)`,
              }}>
                <div style={{ fontSize: 72 }}>{ic}</div>
                <div style={{ fontFamily: TITULO, fontSize: 46, fontWeight: 700, color: COR.texto, margin: '18px 0 10px' }}>{t}</div>
                <div style={{ fontFamily: FONTE, fontSize: 30, color: COR.texto2 }}>{d}</div>
              </div>
            );
          })}
        </div>
      </div>
    </Palco>
  );
}

// cena genérica: legenda à esquerda, celular(es) à direita
function CenaCelular({ passo, titulo, sub, telas, destaque, rolar = [], dur }) {
  const f = useCurrentFrame();
  return (
    <Palco>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
        <Legenda passo={passo} titulo={titulo} sub={sub} destaque={destaque} />
        <div style={{ display: 'flex', gap: 50, alignItems: 'center', marginRight: 40 }}>
          {telas.map((t, i) => {
            const s = useEntrada(10 + i * 16, { damping: 18, stiffness: 80 });
            const flutua = Math.sin((f + i * 30) / 30) * 8;
            const r = rolar[i] ? trilha(f, [40, dur - 30], [0, rolar[i]]) : 0;
            return <Celular key={t} src={tela(t)} largura={telas.length > 1 ? 400 : 430} rolar={r}
              estilo={{ opacity: s, transform: `translateY(${(1 - s) * 200 + flutua}px) rotate(${(1 - s) * (i ? 6 : -6)}deg)` }} />;
          })}
        </div>
      </div>
    </Palco>
  );
}

// cena genérica: navegador com zoom suave em uma região e legenda sobreposta
function CenaDesktop({ passo, titulo, sub, src, zoom = [1, 1.6], origem = '50% 45%', destaque, inverter = false, dur, larguraNav = 1150 }) {
  const f = useCurrentFrame();
  const s = useEntrada(4, { damping: 20, stiffness: 70 });
  const esc = trilha(f, [20, dur - 10], zoom);
  return (
    <Palco>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexDirection: inverter ? 'row-reverse' : 'row', gap: 60 }}>
        <Legenda passo={passo} titulo={titulo} sub={sub} largura={560} />
        <Navegador src={src} largura={larguraNav} escala={esc} origem={origem}
          estilo={{ opacity: s, transform: `translateX(${(1 - s) * (inverter ? -200 : 200)}px) perspective(2000px) rotateY(${(1 - s) * (inverter ? 10 : -10)}deg)` }}>
          {destaque && <Destaque {...destaque} />}
        </Navegador>
      </div>
    </Palco>
  );
}

// totem: check-in → balança → caixa em sequência dentro da mesma cena
function Totem({ dur }) {
  const f = useCurrentFrame();
  const etapas = [
    { src: '05-terminal-entrada', passo: '3 · Entrada', titulo: 'Check-in em um toque', sub: 'O totem lê o QR ou o código digitado.' },
    { src: '06-terminal-checkin', passo: '3 · Entrada', titulo: 'Chegada registrada', sub: 'Com opção de comprovante impresso.' },
    { src: '08-terminal-balanca-ok', passo: '4 · Balança', titulo: 'Fim do buffet', sub: 'Etapa opcional, mede o tempo até a balança.' },
    { src: '10-terminal-caixa-ok', passo: '5 · Caixa', titulo: 'Saída com a mesa', sub: 'A mesa vai para a lista de limpeza.' },
  ];
  const fatia = dur / etapas.length;
  const i = Math.min(etapas.length - 1, Math.floor(f / fatia));
  const local = f - i * fatia;
  const e = etapas[i];
  const entra = Math.min(1, local / 10);
  const esc = trilha(local, [0, fatia], [1.25, 1.55]);
  const s = useEntrada(0, { damping: 20, stiffness: 70 });
  return (
    <Palco>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', gap: 60 }}>
        <div key={i} style={{ opacity: entra }}>
          <Legenda passo={e.passo} titulo={e.titulo} sub={e.sub} largura={560} atraso={i * fatia} />
        </div>
        <Navegador src={tela(e.src)} largura={1150} escala={esc} origem="50% 48%"
          estilo={{ opacity: s, transform: `translateX(${(1 - s) * 200}px)` }} />
      </div>
      <div style={{ position: 'absolute', left: 120, bottom: 80, display: 'flex', gap: 14 }}>
        {etapas.map((_, k) => <div key={k} style={{ width: k === i ? 70 : 24, height: 8, borderRadius: 4, background: k <= i ? COR.ambar : COR.linha }} />)}
      </div>
    </Palco>
  );
}

// espontâneo: tela do totem + comprovante deslizando
function Espontaneo({ dur }) {
  const f = useCurrentFrame();
  const n = useEntrada(8, { damping: 20, stiffness: 70 });
  const p = useEntrada(70, { damping: 14, stiffness: 80 });
  return (
    <Palco>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
        <Legenda passo="Sem app?" titulo="Código na hora, com comprovante." sub="O espontâneo entra pelo totem e guarda o código para avaliar depois." destaque={[3, 4]} largura={620} />
        <div style={{ position: 'relative', width: 1000, height: 760 }}>
          <Navegador src={tela('11-terminal-espontaneo')} largura={900} escala={trilha(f, [10, dur], [1.3, 1.5])} origem="50% 40%"
            estilo={{ position: 'absolute', left: 0, top: 80, opacity: n, transform: `translateY(${(1 - n) * 100}px)` }} />
          <div style={{
            position: 'absolute', right: 0, top: 0, width: 330, background: '#fff', padding: 16, borderRadius: 8,
            boxShadow: '0 50px 100px -30px rgba(0,0,0,.9)', opacity: p, transform: `translateY(${(1 - p) * -260}px) rotate(${4 - p * 1}deg)`,
          }}>
            <Img src={tela('12-comprovante')} style={{ width: '100%' }} />
          </div>
        </div>
      </div>
    </Palco>
  );
}

// dashboard: varredura e destaques
function Dashboard({ dur }) {
  const f = useCurrentFrame();
  const meio = Math.floor(dur / 2);
  const primeira = f < meio;
  const local = primeira ? f : f - meio;
  const esc = trilha(local, [0, meio], primeira ? [1, 1.35] : [1, 1.25]);
  const s = useEntrada(0, { damping: 20, stiffness: 60 });
  const troca = interpolate(f, [meio - 8, meio + 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <Palco>
      <div style={{ position: 'absolute', left: 120, right: 120, top: 70, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Sobretitulo>Gestão em tempo real</Sobretitulo>
        {primeira
          ? <Chip key="a" atraso={20}>Chegadas previstas × reais, a cada 15 min</Chip>
          : <Chip key="b" atraso={meio + 16}>Insights gerados por regras sobre os dados</Chip>}
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 160, display: 'flex', justifyContent: 'center' }}>
        <div style={{ position: 'relative', opacity: s, transform: `scale(${0.92 + s * 0.08})` }}>
          <div style={{ opacity: 1 - troca }}>
            <Navegador src={tela('20-dashboard-hoje')} largura={1320} escala={esc} origem="35% 55%">
              <Destaque x={17.5} y={34} w={53} h={40} atraso={30} />
            </Navegador>
          </div>
          {troca > 0 && (
            <div style={{ opacity: troca, position: 'absolute', inset: 0 }}>
              <Navegador src={tela('22-dashboard-analise')} largura={1320} escala={esc} origem="40% 40%">
                <Destaque x={17.5} y={32} w={81} h={39} atraso={meio + 26} />
              </Navegador>
            </div>
          )}
        </div>
      </div>
    </Palco>
  );
}

// TVs
function TVs({ dur }) {
  const f = useCurrentFrame();
  const meio = Math.floor(dur / 2);
  const a = useEntrada(0, { damping: 20, stiffness: 60 });
  const desliza = trilha(f, [meio - 12, meio + 12], [0, 1]);
  const moldura = (src, extra) => (
    <div style={{ width: 1460, padding: '14px 14px 20px', borderRadius: 20, background: '#050404', border: `1px solid ${COR.linha}`, boxShadow: '0 60px 120px -40px rgba(0,0,0,.9)', position: 'relative', overflow: 'hidden', ...extra }}>
      <Img src={tela(src)} style={{ width: '100%', display: 'block', borderRadius: 6 }} />
    </div>
  );
  return (
    <Palco>
      <div style={{ position: 'absolute', left: 120, top: 80, display: 'flex', alignItems: 'center', gap: 30 }}>
        <Sobretitulo>Modo TV</Sobretitulo>
        <div style={{ fontFamily: TITULO, fontSize: 44, color: COR.texto, fontWeight: 700 }}>{f < meio ? 'TV Cozinha' : 'TV Salão'}</div>
      </div>
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', paddingTop: 110 }}>
        <div style={{ position: 'relative', width: 1460, height: 860 }}>
          <div style={{ position: 'absolute', inset: 0, opacity: a * (1 - desliza), transform: `translateX(${-desliza * 300}px) scale(${0.95 + a * 0.05})` }}>
            {moldura('26-tv-cozinha')}
          </div>
          <div style={{ position: 'absolute', inset: 0, opacity: desliza, transform: `translateX(${(1 - desliza) * 300}px)` }}>
            {moldura('27-tv-salao')}
            {f > meio + 20 && <div style={{ position: 'absolute', left: 14, top: 14, right: 14, height: 822, overflow: 'hidden' }}><Destaque x={60} y={38} w={38} h={61} atraso={meio + 26} /></div>}
          </div>
        </div>
      </AbsoluteFill>
      <div style={{ position: 'absolute', right: 120, top: 84 }}>
        {f < meio
          ? <Chip key="c" atraso={18}>Previstas na próxima hora · prato mais desejado</Chip>
          : <Chip key="d" atraso={meio + 18}>Mesas saem da lista sozinhas em 45 min</Chip>}
      </div>
    </Palco>
  );
}

// arquitetura + honestidade dos dados
function Bastidores() {
  const itens = [['🐍', 'Python + SQLite', 'biblioteca padrão, um único processo'], ['🔒', 'Login com papéis', 'gerente e atendente'], ['✅', '21 testes automatizados', 'jornada, regras e indicadores'], ['🌐', 'Sem serviços externos', 'roda na rede local da casa']];
  return (
    <Palco>
      <div style={{ width: '100%' }}>
        <Sobretitulo>Por baixo do capô</Sobretitulo>
        <div style={{ fontFamily: TITULO, fontSize: 84, fontWeight: 700, color: COR.texto, margin: '24px 0 60px', letterSpacing: -2 }}>
          <Palavras texto="Simples de propósito." atraso={6} destaque={[2]} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 28 }}>
          {itens.map(([ic, t, d], i) => {
            const s = useEntrada(30 + i * 10, { damping: 16 });
            return (
              <div key={t} style={{ display: 'flex', gap: 28, alignItems: 'center', padding: '30px 36px', borderRadius: 28, background: COR.bg2, border: `1px solid ${COR.linha}`, opacity: s, transform: `translateX(${(1 - s) * (i % 2 ? 80 : -80)}px)` }}>
                <div style={{ fontSize: 60 }}>{ic}</div>
                <div><div style={{ fontFamily: TITULO, fontSize: 40, fontWeight: 700, color: COR.texto }}>{t}</div>
                  <div style={{ fontFamily: FONTE, fontSize: 28, color: COR.texto2 }}>{d}</div></div>
              </div>
            );
          })}
        </div>
      </div>
    </Palco>
  );
}

// encerramento
function Encerramento() {
  const s = useEntrada(4, { damping: 14 });
  const n = useEntrada(30);
  const r = useEntrada(54);
  return (
    <AbsoluteFill><Fundo />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column', textAlign: 'center', gap: 30 }}>
        <div style={{ transform: `scale(${s})` }}><Marca tamanho={110} /></div>
        <div style={{ fontFamily: TITULO, fontWeight: 700, fontSize: 104, color: COR.texto, letterSpacing: -3, opacity: s }}>Bovinu's Connect</div>
        <div style={{ fontFamily: TITULO, fontSize: 42, color: COR.texto, opacity: n, transform: `translateY(${(1 - n) * 20}px)` }}>
          Janaina Costa · Vitor Nunes · Matheus Vaccari
        </div>
        <div style={{ fontFamily: FONTE, fontSize: 30, color: COR.ambar, opacity: r }}>github.com/jnnkoc/bovinus-connect</div>
        <div style={{ fontFamily: FONTE, fontSize: 22, color: COR.texto3, opacity: r, marginTop: 30 }}>
          Projeto acadêmico · Hackathon FMU 2026.2 · telas com dados simulados · não é material oficial da Bovinu's
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}

// ---------------------------------------------------------------- roteiro (30 fps)
export const CENAS = [
  { d: 150, c: Abertura },
  { d: 270, c: Problema, t: fade() },
  { d: 210, c: Solucao, t: slide({ direction: 'from-right' }) },
  { d: 240, c: p => <CenaCelular {...p} passo="1 · Planejar" titulo="O cliente avisa que vem." sub="Horário, pessoas e até 3 pratos de interesse — preferência declarada." telas={['01-cliente-inicio', '02-cliente-planejar']} destaque={[3, 4]} />, t: wipe({ direction: 'from-left' }) },
  { d: 180, c: p => <CenaCelular {...p} passo="2 · Código" titulo="Um código do começo ao fim." sub="BOV-XXXX com QR: entrada, balança, caixa e avaliação." telas={['03-cliente-codigo']} destaque={[1, 2]} />, t: fade() },
  { d: 420, c: Totem, t: slide({ direction: 'from-bottom' }) },
  { d: 240, c: Espontaneo, t: fade() },
  { d: 240, c: p => <CenaCelular {...p} passo="6 · Minha visita" titulo="Cadastro depois, fidelidade sempre." sub="Visitas contam no check-out. Cada avaliação vale 1 ponto." telas={['17-minha-visita-cadastro', '18-minha-visita-fidelidade']} destaque={[3, 4]} />, t: wipe({ direction: 'from-right' }) },
  { d: 210, c: p => <CenaCelular {...p} passo="7 · Avaliação" titulo="A voz do cliente, por tema." sub="NPS de 0 a 10 e notas para buffet, espera e atendimento." telas={['15-avaliar', '16-avaliar-obrigado']} rolar={[480, 0]} destaque={[4, 5]} />, t: fade() },
  { d: 390, c: Dashboard, t: slide({ direction: 'from-right' }) },
  { d: 330, c: TVs, t: fade() },
  { d: 210, c: Bastidores, t: wipe({ direction: 'from-bottom' }) },
  { d: 210, c: Encerramento, t: fade() },
];
export const DURACAO = CENAS.reduce((s, c) => s + c.d, 0) - (CENAS.length - 1) * T;

export function BovinusConnect() {
  const { fps } = useVideoConfig();
  const f = useCurrentFrame();
  const volume = interpolate(f, [0, 30, DURACAO - 90, DURACAO], [0, 0.55, 0.55, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: COR.bg }}>
      <Audio src={staticFile('musica.mp3')} volume={volume} />
      <TransitionSeries>
        {CENAS.flatMap(({ d, c: Cena, t }, i) => {
          const itens = [];
          if (i > 0) itens.push(<TransitionSeries.Transition key={`t${i}`} presentation={t || fade()} timing={linearTiming({ durationInFrames: T })} />);
          itens.push(<TransitionSeries.Sequence key={`s${i}`} durationInFrames={d}><Cena dur={d} /></TransitionSeries.Sequence>);
          return itens;
        })}
      </TransitionSeries>
    </AbsoluteFill>
  );
}
