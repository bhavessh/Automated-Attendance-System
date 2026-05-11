const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    const html = await page.content();
    fs.writeFileSync('tests/page_dump.html', html);
    await page.screenshot({ path: 'tests/page_screenshot.png', fullPage: true });
    console.log('DUMP: saved page_dump.html and page_screenshot.png');
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('DUMP: FAIL', err.message);
    await browser.close();
    process.exit(2);
  }
})();
