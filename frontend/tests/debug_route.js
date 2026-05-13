const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    console.log('set localStorage before load');
    await page.addInitScript(() => { localStorage.setItem('token','fake-jwt-token-for-tests'); localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' })); });
    console.log('goto root');
    await page.goto('http://localhost:3001', { waitUntil: 'load', timeout: 60000 });
    console.log('root loaded');
    console.log('pushState');
    await page.evaluate((r) => { window.history.pushState({}, '', r); window.dispatchEvent(new PopStateEvent('popstate')); }, '/dashboard');
    await page.waitForTimeout(1000);
    console.log('checking .main-content');
    const info = await page.evaluate(() => {
      const root = document.querySelector('.main-content');
      if (!root) return { error: 'no .main-content' };
      return { text: (root.innerText||'').slice(0,200), rect: root.getBoundingClientRect() };
    });
    console.log('INFO', info);
    await browser.close();
    process.exit(0);
  } catch (e) {
    console.error('ERR', e);
    await browser.close();
    process.exit(2);
  }
})();
