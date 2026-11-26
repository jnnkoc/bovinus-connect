import '@fontsource-variable/inter';
import '@fontsource-variable/sora';
import { Composition } from 'remotion';
import { BovinusConnect, DURACAO } from './Video.jsx';

export const Root = () => (
  <Composition id="BovinusConnect" component={BovinusConnect} durationInFrames={DURACAO} fps={30} width={1920} height={1080} />
);
