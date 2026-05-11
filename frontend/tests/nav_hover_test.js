const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake-jwt-token-for-tests');
      localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
    });
    await page.goto('http://localhost:3001/dashboard', { waitUntil: 'networkidle' });

    // wait for drawer paper then get initial drawer width
    await page.waitForSelector('.MuiDrawer-paper', { timeout: 5000 });
    const initialWidth = await page.$eval('.MuiDrawer-paper', el => window.getComputedStyle(el).width);

    // hover over drawer root
    const drawerRoot = await page.$('.nav-drawer') || await page.$('.MuiDrawer-root');
    if (drawerRoot) await drawerRoot.hover();
    await page.waitForTimeout(300);
    const hoveredWidth = await page.$eval('.MuiDrawer-paper', el => window.getComputedStyle(el).width);

    // click avatar to open menu and take screenshot
    const avatar = await page.$('button[aria-label="account of current user"]');
    if (avatar) await avatar.click();
    await page.waitForTimeout(400);

    await page.screenshot({ path: 'tests/nav_hover.png', fullPage: true });

    console.log('INITIAL_WIDTH:', initialWidth);
    console.log('HOVERED_WIDTH:', hoveredWidth);

    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('TEST-FAIL', err);
    await browser.close();
    process.exit(2);
  }
})();
