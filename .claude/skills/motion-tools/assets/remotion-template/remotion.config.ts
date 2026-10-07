import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setPixelFormat('yuv420p');
Config.setCodec('h264');
Config.setCrf(18);
Config.setColorSpace('bt709');   // sinon yuvj420p plein écart (pc), refusé par check_delivery
// Conteneur cloud : Chromium préinstallé (sinon Remotion télécharge son propre « headless shell »).
if (process.env.REMOTION_CHROMIUM) {
  Config.setBrowserExecutable(process.env.REMOTION_CHROMIUM);
}
