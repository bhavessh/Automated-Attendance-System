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
    await page.evaluate((r) => { window.history.pushState({}, '', r); window.dispatchEvent(new PopStateEvent('popstate')); }, '/students');
    await page.waitForTimeout(800);

    const info = await page.evaluate(() => {
      const root = document.querySelector('.main-content');
      if (!root) return { error: 'no main-content' };
      const rect = root.getBoundingClientRect();
      const style = window.getComputedStyle(root);
      const parents = [];
      let p = root.parentElement;
      while (p) {
        const s = window.getComputedStyle(p);
        parents.push({ tag: p.tagName, cls: p.className, rect: p.getBoundingClientRect(), position: s.position, transform: s.transform, marginTop: s.marginTop });
        p = p.parentElement;
      }
      return { rect, style: { display: style.display, visibility: style.visibility, opacity: style.opacity, color: style.color, background: style.backgroundColor }, parents };
    });

    fs.writeFileSync('tests/maincontent_debug.json', JSON.stringify(info, null, 2));
    console.log('WROTE tests/maincontent_debug.json');
    await browser.close();
    process.exit(0);
  } catch (e) {
    console.error(e);
    await browser.close();
    process.exit(2);
  }
})();
