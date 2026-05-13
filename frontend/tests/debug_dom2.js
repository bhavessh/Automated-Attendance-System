const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await page.addInitScript(() => {
      localStorage.setItem('token','fake-jwt-token-for-tests');
      localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
    });
    await page.goto('http://localhost:3001', { waitUntil: 'load', timeout: 60000 });
    await page.evaluate(() => { window.history.pushState({}, '', '/students'); window.dispatchEvent(new PopStateEvent('popstate')); });
    await page.waitForTimeout(800);

    const details = await page.evaluate(() => {
      const app = document.querySelector('.App');
      if (!app) return { error: 'no .App' };
      const list = [];
      const children = Array.from(app.children);
      for (const el of children) {
        const r = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        list.push({ tag: el.tagName, cls: el.className, id: el.id || null, top: r.top, height: r.height, display: style.display, marginTop: style.marginTop, paddingTop: style.paddingTop });
        // also log first-level descendants of main-content
        if (el.classList && el.classList.contains('main-content')) {
          const inner = Array.from(el.children).map(c => {
            const rc = c.getBoundingClientRect(); const sc = window.getComputedStyle(c);
            return { tag: c.tagName, cls: c.className, top: rc.top, height: rc.height, display: sc.display };
          });
          return { appChildren: list, mainContentChildren: inner };
        }
      }
      return { appChildren: list };
    });

    console.log(JSON.stringify(details, null, 2));

    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error(err);
    await browser.close();
    process.exit(2);
  }
})();
