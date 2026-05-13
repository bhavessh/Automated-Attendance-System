const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const results = [];
  const routes = ['/dashboard','/students','/attendance','/reports','/settings','/admin/add-teacher'];
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    for (const route of routes) {
      const url = `http://localhost:3001${route}`;
      console.log('Visiting', url);
      // ensure auth is present before the app mounts
      await page.addInitScript(() => {
        localStorage.setItem('token','fake-jwt-token-for-tests');
        localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
      });
      // load root to ensure app JS is available
      await page.goto('http://localhost:3001', { waitUntil: 'load', timeout: 60000 });
      // navigate client-side to route to avoid dev-server 404 for deep links
      await page.evaluate((r) => {
        window.history.pushState({}, '', r);
        window.dispatchEvent(new PopStateEvent('popstate'));
      }, route);
      // give React time to render the route
      await page.waitForTimeout(1000);
      await page.waitForTimeout(400);

      // screenshot
      const fileName = route.replace(/\//g, '_').replace(/^_/, '') || 'root';
      const screenshotPath = `${fileName}.png`;
      await page.screenshot({ path: screenshotPath, fullPage: true });

      // extract main-content info
      const info = await page.evaluate(() => {
        const root = document.querySelector('.main-content');
        if (!root) return { error: 'no .main-content' };
        const rect = root.getBoundingClientRect();
        const text = (root.innerText || '').trim().replace(/\s+/g,' ').slice(0,1000);
        const style = window.getComputedStyle(root);
        return {
          textSnippet: text,
          width: rect.width,
          height: rect.height,
          display: style.display,
          visibility: style.visibility,
          opacity: style.opacity,
          color: style.color,
          background: style.backgroundColor
        };
      });

      results.push({ route, url, screenshot: screenshotPath, info });
    }

    fs.writeFileSync('tests/batch_results.json', JSON.stringify(results, null, 2));
    console.log('DONE');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('ERROR', err.message);
    fs.writeFileSync('tests/batch_results.json', JSON.stringify({ error: err.message }, null, 2));
    await browser.close();
    process.exit(2);
  }
})();
