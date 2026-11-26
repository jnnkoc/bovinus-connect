import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing } from 'remotion';

export const COR = {
  bg: '#0e0a0a', bg2: '#1a1415', texto: '#f7efe8', texto2: '#c4b4aa', texto3: '#8f7f77',
  ambar: '#eaa53f', brasa: '#e0523a', bordo: '#8c1f26', verde: '#4cc38a', linha: 'rgba(255,240,230,.12)',
};
export const GRAD = 'linear-gradient(120deg, #f2b552 0%, #e0523a 55%, #a3242c 100%)';
export const TITULO = '"Sora Variable", "Segoe UI", sans-serif';
export const FONTE = '"Inter Variable", "Segoe UI", sans-serif';
const suave = Easing.bezier(0.22, 1, 0.36, 1);

export const tela = nome => staticFile(`telas/${nome}.png`);

// entrada com mola (0 → 1), a partir de `atraso` quadros
export function useEntrada(atraso = 0, config = { damping: 200 }) {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: f - atraso, fps, config });
}

// saída: 1 → 0 nos últimos `dur` quadros da cena
export function useSaida(duracaoCena, dur = 12) {
  const f = useCurrentFrame();
  return interpolate(f, [duracaoCena - dur, duracaoCena], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
}

export function Fundo({ tom = 0 }) {
  const f = useCurrentFrame();
  const x = Math.sin(f / 90) * 60;
  const y = Math.cos(f / 110) * 40;
  return (
    <AbsoluteFill style={{ background: COR.bg, overflow: 'hidden' }}>
      <div style={{
        position: 'absolute', width: 1100, height: 1100, borderRadius: '50%', filter: 'blur(140px)', opacity: .5,
        background: '#a3242c', right: -320 + x, top: -420 + y,
      }} />
      <div style={{
        position: 'absolute', width: 800, height: 800, borderRadius: '50%', filter: 'blur(150px)', opacity: .22 + tom * .1,
        background: '#c9772a', left: -300 - x, bottom: -380 - y,
      }} />
      <AbsoluteFill style={{
        opacity: .25,
        backgroundImage: `linear-gradient(${COR.linha} 1px, transparent 1px), linear-gradient(90deg, ${COR.linha} 1px, transparent 1px)`,
        backgroundSize: '80px 80px', backgroundPosition: `${-f * .3}px ${-f * .3}px`,
        maskImage: 'radial-gradient(ellipse 70% 60% at 50% 40%, #000 20%, transparent 75%)',
        WebkitMaskImage: 'radial-gradient(ellipse 70% 60% at 50% 40%, #000 20%, transparent 75%)',
      }} />
    </AbsoluteFill>
  );
}

// texto que entra palavra por palavra
export function Palavras({ texto, atraso = 0, passo = 3, estilo = {}, destaque = [] }) {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <span style={{ display: 'inline', ...estilo }}>
      {texto.split(' ').map((p, i) => {
        const s = spring({ frame: f - atraso - i * passo, fps, config: { damping: 200 } });
        const quente = destaque.includes(i);
        return (
          <span key={i} style={{
            display: 'inline-block', marginRight: '0.26em', opacity: s, transform: `translateY(${(1 - s) * 40}px)`,
            ...(quente ? { background: GRAD, WebkitBackgroundClip: 'text', color: 'transparent' } : {}),
          }}>{p}</span>
        );
      })}
    </span>
  );
}

export function Sobretitulo({ children, atraso = 0 }) {
  const s = useEntrada(atraso);
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, color: COR.ambar, fontFamily: FONTE, fontWeight: 700,
      fontSize: 24, letterSpacing: 5, textTransform: 'uppercase', opacity: s, transform: `translateX(${(1 - s) * -30}px)`,
    }}>
      <span style={{ width: 44 * s, height: 3, background: GRAD, borderRadius: 3 }} />
      {children}
    </div>
  );
}

// legenda lateral: passo + título + subtítulo
export function Legenda({ passo, titulo, sub, atraso = 6, largura = 640, destaque = [] }) {
  const s = useEntrada(atraso + 10);
  return (
    <div style={{ width: largura, fontFamily: FONTE }}>
      {passo && <Sobretitulo atraso={atraso}>{passo}</Sobretitulo>}
      <div style={{ fontFamily: TITULO, fontSize: 68, lineHeight: 1.08, fontWeight: 700, color: COR.texto, margin: '22px 0 22px', letterSpacing: -1.5 }}>
        <Palavras texto={titulo} atraso={atraso + 4} destaque={destaque} />
      </div>
      {sub && <div style={{ fontSize: 30, lineHeight: 1.4, color: COR.texto2, opacity: s, transform: `translateY(${(1 - s) * 20}px)` }}>{sub}</div>}
    </div>
  );
}

// celular com rolagem opcional da imagem (rolar: fração 0..1 da altura excedente)
export function Celular({ src, largura = 430, rolar = 0, estilo = {} }) {
  const altura = largura * (880 / 412);
  return (
    <div style={{
      width: largura + 24, padding: 12, borderRadius: 64, background: '#1a1314',
      boxShadow: '0 60px 120px -40px rgba(0,0,0,.9), inset 0 0 0 2px #2c2223', border: `1px solid ${COR.linha}`, ...estilo,
    }}>
      <div style={{ width: largura, height: altura, borderRadius: 52, overflow: 'hidden', position: 'relative', background: '#f7efe4' }}>
        <Img src={src} style={{ width: '100%', position: 'absolute', top: 0, transform: `translateY(${-rolar}px)` }} />
      </div>
    </div>
  );
}

// janela de navegador com zoom (escala) e foco (origem em %)
export function Navegador({ src, largura = 1240, escala = 1, origem = '50% 50%', estilo = {}, children }) {
  return (
    <div style={{
      width: largura, borderRadius: 22, overflow: 'hidden', background: '#241b1c',
      boxShadow: '0 60px 120px -40px rgba(0,0,0,.9)', border: `1px solid ${COR.linha}`, ...estilo,
    }}>
      <div style={{ display: 'flex', gap: 10, padding: '14px 18px', background: '#2b2122' }}>
        {['#e0523a', '#eaa53f', '#5a4a47'].map(c => <span key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />)}
      </div>
      <div style={{ overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'relative', transform: `scale(${escala})`, transformOrigin: origem }}>
          <Img src={src} style={{ width: '100%', display: 'block' }} />
          {children}
        </div>
      </div>
    </div>
  );
}

// anel que destaca uma região (coordenadas em % da imagem)
export function Destaque({ x, y, w, h, atraso = 0 }) {
  const f = useCurrentFrame();
  const s = useEntrada(atraso, { damping: 14, stiffness: 120 });
  const pulso = 1 + Math.sin((f - atraso) / 8) * 0.012;
  return (
    <div style={{
      position: 'absolute', left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%`, borderRadius: 18,
      border: `4px solid ${COR.ambar}`, boxShadow: '0 0 0 9999px rgba(10,6,6,.45), 0 0 40px rgba(234,165,63,.6)',
      opacity: s, transform: `scale(${(0.9 + s * 0.1) * pulso})`,
    }} />
  );
}

// interpola com easing suave entre pares [quadro, valor]
export function trilha(f, quadros, valores) {
  return interpolate(f, quadros, valores, { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: suave });
}

export function Chip({ children, atraso = 0, cor = COR.ambar }) {
  const s = useEntrada(atraso, { damping: 16 });
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 12, padding: '14px 26px', borderRadius: 999, fontFamily: FONTE,
      fontWeight: 650, fontSize: 28, color: cor, border: `2px solid ${cor}55`, background: `${cor}14`,
      opacity: s, transform: `scale(${0.8 + s * 0.2})`,
    }}>{children}</div>
  );
}
