#!/usr/bin/env node
/* Rendu image par image du film HTML (mywebtel/film/index.html) avec Chromium + ffmpeg.
 *
 *   node mywebtel/render.js --stills 2.5,17.2,44          images fixes -> build/mywebtel/stills/
 *   node mywebtel/render.js --range 38 54                  passage -> build/mywebtel/preview_38_54.mp4
 *   node mywebtel/render.js                                film complet -> build/mywebtel/video_silent.mp4
 * Options : --workers N (défaut 3), --fps 30.
 * Chromium : CHROMIUM=/chemin/vers/chrome (défaut : le Chromium préinstallé du conteneur).
 */
const { chromium } = require("playwright-core");
const fs = require("fs"), path = require("path"), cp = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "build", "mywebtel");
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const FPS = +opt("--fps", 30), WORKERS = +opt("--workers", 3);
const TL = JSON.parse(fs.readFileSync(path.join(OUT, "timeline.json"), "utf8"));
const EXE = process.env.CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";

async function openPage(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  page.on("pageerror", e => { console.error("erreur dans la page :", e.message); process.exitCode = 1; });
  await page.addInitScript(`window.TL = ${JSON.stringify(TL)};`);
  await page.goto("file://" + path.join(ROOT, "mywebtel", "film", "index.html"));
  await page.waitForFunction(() => window.READY === true, null, { timeout: 30000 });
  return page;
}
const shot = async (page, t) => { await page.evaluate(t => window.renderAt(t), t); return page.screenshot({ type: "jpeg", quality: 94 }); };

async function renderRange(browser, n0, n1, file) {
  const page = await openPage(browser);
  const ff = cp.spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-color_range", "tv", file], { stdio: ["pipe", "inherit", "inherit"] });
  for (let n = n0; n < n1; n++) {
    const buf = await shot(page, n / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on("close", c => c ? rej(new Error("ffmpeg " + c)) : res()));
  await page.context().close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ["--no-sandbox", "--force-color-profile=srgb", "--disable-lcd-text", "--font-render-hinting=none"] });
  const t0 = Date.now();
  {                                                     // repères du film pour les bruitages (sfx_mix.py)
    const page = await openPage(browser);
    fs.writeFileSync(path.join(OUT, "cues.json"), JSON.stringify(await page.evaluate(() => window.FILM), null, 1));
    await page.context().close();
  }
  if (args.includes("--stills")) {
    const dir = path.join(OUT, "stills"); fs.mkdirSync(dir, { recursive: true });
    const page = await openPage(browser);
    for (const t of opt("--stills").split(",").map(Number)) {
      const f = path.join(dir, "t" + t.toFixed(2).padStart(6, "0") + ".jpg");
      fs.writeFileSync(f, await shot(page, t));
      console.log(f);
    }
  } else {
    let a = 0, b = TL.duration, out = path.join(OUT, "video_silent.mp4");
    if (args.includes("--range")) { const i = args.indexOf("--range"); a = +args[i + 1]; b = +args[i + 2]; out = path.join(OUT, `preview_${a}_${b}.mp4`); }
    const n0 = Math.round(a * FPS), n1 = Math.round(b * FPS), per = Math.ceil((n1 - n0) / WORKERS);
    const parts = [];
    for (let w = 0; w < WORKERS; w++) {
      const s = n0 + w * per, e = Math.min(n1, s + per);
      if (s < e) parts.push({ s, e, file: path.join(OUT, `part_${w}.mp4`) });
    }
    await Promise.all(parts.map(p => renderRange(browser, p.s, p.e, p.file)));
    const list = path.join(OUT, "parts.txt");
    fs.writeFileSync(list, parts.map(p => `file '${p.file}'`).join("\n"));
    cp.execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy", "-movflags", "+faststart", out]);
    parts.forEach(p => fs.unlinkSync(p.file));
    console.log(`-> ${out} (${n1 - n0} images en ${((Date.now() - t0) / 1000).toFixed(0)} s)`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
