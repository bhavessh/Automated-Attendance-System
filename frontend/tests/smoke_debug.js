const { chromium } = require('playwright');

(async () => {
  console.log('SMOKE_DEBUG: starting');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    console.log('SMOKE_DEBUG: opening app');
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    console.log('SMOKE_DEBUG: setting localStorage');
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake-jwt-token-for-tests');
      localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
    });
    console.log('SMOKE_DEBUG: navigating to /students');
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });

    console.log('SMOKE_DEBUG: looking for avatar');
    const sel = 'button[aria-label="account of current user"]';
    const el = await page.$(sel);
    console.log('SMOKE_DEBUG: avatar element:', !!el);
    if (!el) throw new Error('Avatar not found');
    await el.click();
    await page.waitForTimeout(500);
    const menu = await page.$('div[role="menu"], .MuiMenu-root, ul[role="menu"]');
    console.log('SMOKE_DEBUG: menu found:', !!menu);
    if (!menu) throw new Error('User menu did not appear after clicking avatar');

    console.log('SMOKE_DEBUG: looking for Add Student button');
    const addBtn = await page.$('button#add-student, button[aria-label="Add Student"], button:has-text("Add Student")');
    console.log('SMOKE_DEBUG: add button found:', !!addBtn);
    if (!addBtn) throw new Error('Add Student button not found');
    await addBtn.click();
    await page.waitForTimeout(500);
    const dialog = await page.$('dialog, .MuiDialog-root, [role="dialog"]');
    console.log('SMOKE_DEBUG: dialog found:', !!dialog);
    if (!dialog) throw new Error('Add Student dialog did not appear');

    console.log('SMOKE_DEBUG: PASS');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('SMOKE_DEBUG: FAIL', err.message);
    await browser.close();
    process.exit(2);
  }
})();
