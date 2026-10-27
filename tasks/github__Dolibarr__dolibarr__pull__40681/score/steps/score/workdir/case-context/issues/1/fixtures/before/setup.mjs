import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
export default async function setup() {
  // Prepared demo account documented in dev/initdemo/README.md; admin/admin verified.
  await browser('open', 'http://localhost:8000/');
  await browser('fill', 'input[name="username"]', 'admin');
  await browser('fill', 'input[name="password"]', 'admin');
  await browser('click', 'input[type="submit"]');
  await browser('wait', '--load', 'networkidle');
  await browser('find', 'role', 'link', 'click', '--name', 'Products | Services', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--url', 'http://localhost:8000/product/index.php?mainmenu=products&leftmenu=');
  await browser('find', 'role', 'link', 'click', '--name', 'Replenishment', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--url', 'http://localhost:8000/product/stock/replenish.php?leftmenu=');
  await browser('find', 'role', 'link', 'click', '--name', 'Use physical stock', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', 'input[name="tobuy0"]');
  await browser('wait', '--url', 'http://localhost:8000/product/stock/replenish.php?mode=physical');
}
