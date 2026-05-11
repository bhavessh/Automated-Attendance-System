const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });
    await page.evaluate(() => {
      localStorage.setItem('token', 'fake-jwt-token-for-tests');
      localStorage.setItem('user', JSON.stringify({ full_name: 'Test User', role: 'admin' }));
    });
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });
    await page.waitForTimeout(300);
    const result = await page.evaluate(() => {
      const root = document.querySelector('.main-content');
      if (!root) return { error: 'no .main-content' };
      const children = Array.from(root.querySelectorAll('*')).slice(0,200);
      const items = children.map((el) => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        return {
          tag: el.tagName,
          classes: el.className,
          textSnippet: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0,120),
          visible: !(style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0' || rect.width===0 && rect.height===0),
          width: rect.width,
          height: rect.height,
          color: style.color,
          background: style.backgroundColor,
          position: style.position
        };
      });
      return { count: children.length, items };
    });
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('ERROR', err.message);
    await browser.close();
    process.exit(2);
  }
})();
