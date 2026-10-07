import {AbsoluteFill, Easing, Img, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {BEAT} from './Root';

const PAPER = '#FAF6F0';

// Un look « sticker » : entrée en ressort sur le temps fort, tenue vivante, sortie accélérée.
const Sticker: React.FC<{src: string; color: string; hold: number}> = ({src, color, hold}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 12, stiffness: 180, mass: 0.8}}); // ~10 % de dépassement
  const exit = interpolate(frame, [hold - 8, hold], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic),
  });
  const float = Math.sin(frame / 14) * 8;                       // tenue vivante (±8 px)
  const scale = interpolate(enter, [0, 1], [0.55, 1]) * (1 - 0.4 * exit);
  const rot = interpolate(enter, [0, 1], [-14, -3]) + 120 * exit;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <div style={{
        position: 'absolute', width: 900, height: 900, borderRadius: '50%', background: color, opacity: 0.45,
        transform: `scale(${interpolate(enter, [0, 1], [0.6, 1])})`, top: 935 - 450,
      }} />
      <Img src={staticFile(src)} style={{
        height: 1230, position: 'absolute', top: 935 - 615 + float,
        transform: `rotate(${rot}deg) scale(${scale})`, opacity: 1 - exit,
        filter: 'drop-shadow(10px 14px 0 rgba(0,0,0,0.25))',
      }} />
    </AbsoluteFill>
  );
};

export const Film: React.FC<{looks: string[]}> = ({looks}) => {
  const colors = ['#F0287F', '#3D8BFF', '#14A89A', '#FF7A00'];
  const bar = 4 * BEAT;                                          // un look par mesure (2 s)
  return (
    <AbsoluteFill style={{backgroundColor: PAPER}}>
      {looks.map((src, i) => (
        <Sequence key={src} from={i * bar} durationInFrames={bar}>
          <Sticker src={src} color={colors[i % colors.length]} hold={bar} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
