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
    // ensure route mounted
    await page.evaluate(() => { window.history.pushState({}, '', '/students'); window.dispatchEvent(new PopStateEvent('popstate')); });
    await page.waitForTimeout(800);

    const topElements = await page.evaluate(() => {
      const els = Array.from(document.body.children).map((el, i) => {
        const r = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        return {
          index: i,
          tag: el.tagName,
          id: el.id || null,
          class: el.className || null,
          width: r.width,
          height: r.height,
          top: r.top,
          bottom: r.bottom,
          display: style.display,
          position: style.position,
          marginTop: style.marginTop,
        };
      });
      return els.slice(0, 40);
    });

    console.log('Top-level body children (index, tag, id, class, top, height):');
    topElements.forEach(e => console.log(e.index, e.tag, e.id, e.class, 'top='+Math.round(e.top), 'h='+Math.round(e.height), 'pos='+e.position));

    // find element at y=100 (near top) and y=400 (mid) and y=700 (where blank shows)
    const points = [100, 400, 700, 900];
    for (const y of points) {
      const el = await page.evaluate((yy) => {
        const found = document.elementsFromPoint(window.innerWidth/2, yy)[0];
        if (!found) return { y: yy, tag: null };
        return { y: yy, tag: found.tagName, id: found.id || null, cls: found.className || null };
      }, y);
      console.log('element at y=', y, el);
    }

    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error(err);
    await browser.close();
    process.exit(2);
  }
})();
