import {Composition} from 'remotion';
import {Film} from './Film';

// 9:16, 30 i/s, 120 BPM : 1 temps = 15 images, 1 mesure = 60 images (2 s par look)
export const FPS = 30;
export const BEAT = 15;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Film"
    component={Film}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={2 * 4 * BEAT}
    defaultProps={{looks: ['look_a.png', 'look_b.png']}}
  />
);
