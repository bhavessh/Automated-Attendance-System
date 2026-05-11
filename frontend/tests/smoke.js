const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    // Inject fake auth so app shows the students page without real backend login
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake-jwt-token-for-tests');
      localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
    });
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });

    // Try several selectors to find the avatar and click it
    const avatarSelectors = [
      'button[aria-label="account of current user"]',
      'button[aria-label^="account"]',
      'header img',
      '.MuiAvatar-root',
      '[data-testid="avatar"]',
      '.appbar-avatar',
      'button[title="Account"]',
      '.user-avatar'
    ];

    let found = false;
    for (const sel of avatarSelectors) {
      const el = await page.$(sel);
      if (el) {
        await el.click();
        found = true;
        break;
      }
    }
    if (!found) throw new Error('Avatar not found');

    // Wait a short moment for menu to appear
    await page.waitForTimeout(600);
    const menu = await page.$('div[role="menu"], .MuiMenu-root, ul[role="menu"]');
    if (!menu) throw new Error('User menu did not appear after clicking avatar');

    // Try to locate and click the Add Student button
    const addSelectors = [
      'button#add-student',
      'button[aria-label="Add Student"]',
      'button:has-text("Add Student")',
      'button:has-text("Add student")',
      '.add-student'
    ];
    found = false;
    for (const sel of addSelectors) {
      const btn = await page.$(sel);
      if (btn) {
        await btn.click();
        found = true;
        break;
      }
    }
    if (!found) {
      // As a fallback, try common page-level Add buttons
      const btn = await page.$('button:has-text("Add")');
      if (btn) {
        await btn.click();
        found = true;
      }
    }
    if (!found) throw new Error('Add Student button not found/clickable');

    await page.waitForTimeout(600);
    const dialog = await page.$('dialog, .MuiDialog-root, [role="dialog"]');
    if (!dialog) throw new Error('Add Student dialog did not appear');

    console.log('SMOKE_TEST: PASS');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('SMOKE_TEST: FAIL', err.message);
    await browser.close();
    process.exit(2);
  }
})();
