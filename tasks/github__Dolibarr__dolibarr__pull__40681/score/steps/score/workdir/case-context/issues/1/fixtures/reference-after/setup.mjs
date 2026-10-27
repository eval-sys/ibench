import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
const appURL = (process.env.APP_URL || 'http://localhost:8000').replace(/\/$/, '');
const productRow = 'tr:has(a[href="/product/stock/product.php?id=10"])';
export default async function setup() {
  // Prepared demo account documented in dev/initdemo/README.md; admin/admin verified.
  await browser('open', `${appURL}/`);
  await browser('fill', 'input[name="username"]', 'admin');
  await browser('fill', 'input[name="password"]', 'admin');
  await browser('click', 'input[type="submit"]');
  await browser('wait', '--load', 'networkidle');
  await browser('find', 'role', 'link', 'click', '--name', 'Products | Services', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--url', `${appURL}/product/index.php?mainmenu=products&leftmenu=`);
  await browser('find', 'role', 'link', 'click', '--name', 'Replenishment', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--url', `${appURL}/product/stock/replenish.php?leftmenu=`);
  await browser('find', 'role', 'link', 'click', '--name', 'Use physical stock', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', `${productRow} input[name^="tobuy"]`);
  await browser('wait', '--url', `${appURL}/product/stock/replenish.php?mode=physical`);
  const rowText = (await browser('get', 'text', productRow)).stdout;
  if (!rowText.includes('COMP-XP4523') || !rowText.includes('Computer XP4523')) {
    throw new Error('Prepared product is not present in the physical-stock row');
  }
  for (const [selector, expected] of [
    ['td:nth-child(4)', '200'], ['td:nth-child(5)', '150'],
    ['td:nth-child(6)', '110.00'], ['td:nth-child(7) a', '100'],
  ]) {
    const actual = (await browser('get', 'text', `${productRow} ${selector}`)).stdout.trim();
    if (!actual.includes(expected)) throw new Error(`Given mismatch for ${selector}: ${actual}`);
  }
  console.log(`Physical-stock Given: ${rowText.trim()}`);
}

