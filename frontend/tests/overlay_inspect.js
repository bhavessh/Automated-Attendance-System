const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await page.addInitScript(() => {
      localStorage.setItem('token','fake-jwt-token-for-tests');
      localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
    });
    await page.goto('http://localhost:3001', { waitUntil: 'load', timeout: 60000 });
    // navigate client-side
    await page.evaluate((r) => { window.history.pushState({}, '', r); window.dispatchEvent(new PopStateEvent('popstate')); }, '/students');
    await page.waitForTimeout(800);

    const report = await page.evaluate(() => {
      const centerX = Math.floor(window.innerWidth / 2);
      const centerY = Math.floor(window.innerHeight / 2);

      const elemsAtCenter = document.elementsFromPoint(centerX, centerY).map(e => {
        const s = window.getComputedStyle(e);
        const r = e.getBoundingClientRect();
        return {
          tag: e.tagName,
          id: e.id || null,
          class: e.className || null,
          zIndex: s.zIndex,
          pointerEvents: s.pointerEvents,
          background: s.backgroundColor || s.background,
          opacity: s.opacity,
          rect: { x: r.x, y: r.y, width: r.width, height: r.height }
        };
      });

      // find top-level elements with high z-index that overlap the center
      const candidates = Array.from(document.querySelectorAll('body *')).map(e => {
        const s = window.getComputedStyle(e);
        const r = e.getBoundingClientRect();
        return { el: e, z: s.zIndex === 'auto' ? null : Number(s.zIndex), pointerEvents: s.pointerEvents, bg: s.backgroundColor || s.background, rect: r };
      }).filter(x => x.z !== null && x.z >= 1000).map(x => ({ tag: x.el.tagName, cls: x.el.className, z: x.z, pointerEvents: x.pointerEvents, bg: x.bg, rect: { x: x.rect.x, y: x.rect.y, width: x.rect.width, height: x.rect.height } }));

      // find any visible backdrops (MuiBackdrop-root)
      const backdrops = Array.from(document.querySelectorAll('.MuiBackdrop-root')).map(e => {
        const s = window.getComputedStyle(e);
        const r = e.getBoundingClientRect();
        return { tag: e.tagName, cls: e.className, zIndex: s.zIndex, pointerEvents: s.pointerEvents, background: s.backgroundColor || s.background, rect: { x: r.x, y: r.y, width: r.width, height: r.height }, ariaHidden: e.getAttribute('aria-hidden') };
      });

      return { center: { x: centerX, y: centerY }, elemsAtCenter, candidates, backdrops };
    });

    fs.writeFileSync('tests/overlay_report.json', JSON.stringify(report, null, 2));
    console.log('WROTE tests/overlay_report.json');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error(err);
    await browser.close();
    process.exit(2);
  }
})();
