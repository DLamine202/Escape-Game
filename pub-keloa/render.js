const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const mode = process.argv[2] || 'preview';
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.resolve('pub.html'));
  await p.evaluate(() => document.fonts.ready);
  if (mode === 'preview') {
    const ts = (process.argv[3] || '1.5,5.5,10,14.8,19').split(',').map(Number);
    for (const t of ts) { await p.evaluate(t => render(t), t); await p.screenshot({ path: `preview_${t}.png` }); }
  } else {
    const fps = 30, dur = 20;
    require('fs').mkdirSync('frames', { recursive: true });
    for (let i = 0; i < fps * dur; i++) {
      await p.evaluate(t => render(t), i / fps);
      await p.screenshot({ path: `frames/f${String(i).padStart(4, '0')}.png` });
    }
  }
  await b.close();
})();
