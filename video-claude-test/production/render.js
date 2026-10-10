// Rendu image par image de pub.html (Chromium headless) vers des segments vidéo.
// Usage : node render.js <debut_image> <fin_image> <sortie.mp4>   |   node render.js --stills t1,t2,...
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const FPS = 30;
const timeline = JSON.parse(fs.readFileSync(__dirname + '/timeline.json', 'utf8'));

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.addInitScript(tl => { window.TIMELINE = tl; }, timeline);
  await p.goto('file://' + __dirname + '/pub.html');
  await p.evaluate(() => document.fonts.ready);
  if (process.argv[2] === '--stills') {
    for (const t of process.argv[3].split(',').map(Number)) {
      await p.evaluate(t => window.render(t), t);
      await p.screenshot({ path: `stills/t_${t.toFixed(2)}.png` });
    }
  } else {
    const [a, z, out] = [Number(process.argv[2]), Number(process.argv[3]), process.argv[4]];
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = a; i < z; i++) {
      await p.evaluate(t => window.render(t), i / FPS);
      const img = await p.screenshot({ type: 'jpeg', quality: 94 });
      if (!ff.stdin.write(img)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
  }
  await b.close();
})();
