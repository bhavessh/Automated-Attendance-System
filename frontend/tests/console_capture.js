const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const logs = [];
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('console', msg => logs.push({type: 'console', text: msg.text()}));
  page.on('pageerror', err => logs.push({type: 'pageerror', text: err.message}));
  try {
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });
    await page.evaluate(() => { localStorage.setItem('token','fake-jwt-token-for-tests'); localStorage.setItem('user', JSON.stringify({full_name:'Test User', role:'admin'})); });
    await page.goto('http://localhost:3001/students', { waitUntil: 'networkidle' });
    // interact: click Students nav (by aria-current) then avatar
    const navItem = await page.$('a[aria-current="page"], button[aria-current="page"]');
    if (navItem) { await navItem.click().catch(()=>{}); }
    await page.waitForTimeout(200);
    const avatar = await page.$('button[aria-label="account of current user"]');
    if (avatar) await avatar.click().catch(()=>{});
    await page.waitForTimeout(500);
    await page.screenshot({path:'console_capture.png', fullPage:true});
    logs.push({type:'info', text:'screenshot saved to console_capture.png'});
  } catch (err) {
    logs.push({type:'error', text: err.message});
  } finally {
    await browser.close();
    fs.writeFileSync('console_logs.json', JSON.stringify(logs, null, 2));
    console.log('DONE');
    process.exit(0);
  }
})();
