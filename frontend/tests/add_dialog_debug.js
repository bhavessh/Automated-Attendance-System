const { chromium } = require('playwright');

(async () => {
  console.log('ADD_DIALOG_DEBUG: start');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake-jwt-token-for-tests');
      localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
    });
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });

    // click Add Student (primary header button)
    const btn = await page.$('button:has-text("Add Student")');
    console.log('ADD_DIALOG_DEBUG: button found', !!btn);
    if (!btn) throw new Error('Add button not found');

    await btn.click();
    console.log('ADD_DIALOG_DEBUG: clicked add button');

    // Give time for dialog to open
    await page.waitForTimeout(400);

    const dialogs = await page.$$('[role="dialog"]');
    console.log('ADD_DIALOG_DEBUG: dialog count', dialogs.length);
    for (let i = 0; i < dialogs.length; i++) {
      const el = dialogs[i];
      const text = await el.innerText();
      console.log(`DIALOG[${i}] text snippet:`, text.substring(0, 120).replace(/\n/g, ' '));
      const visible = await el.isVisible();
      console.log(`DIALOG[${i}] visible:`, visible);
      const box = await el.boundingBox();
      console.log(`DIALOG[${i}] bbox:`, box);
    }

    // Also check for MUI classes / portal children
    const portal = await page.$('body > div.MuiDialog-root, body > div[role="presentation"]');
    console.log('ADD_DIALOG_DEBUG: portal found', !!portal);
    if (portal) {
      const portalText = await portal.innerText();
      console.log('ADD_DIALOG_DEBUG: portal snippet', portalText.substring(0, 200).replace(/\n/g, ' '));
    }

    console.log('ADD_DIALOG_DEBUG: done');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('ADD_DIALOG_DEBUG: FAIL', err.message);
    await browser.close();
    process.exit(2);
  }
})();
