import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const execute = promisify(execFile);
async function browser(...args) {
  const { stdout } = await execute('agent-browser', args, { timeout: 60000, maxBuffer: 1024 * 1024 });
  return stdout.trim();
}

export default async function setup() {
  // Endpoint documented in conf.php and /opt/dev-env-profile.sh.
  // Credentials are the prepared native demo's admin/admin account.
  await browser('open', 'http://localhost:8000/index.php');
  await browser('wait', 'input[name="username"]');
  await browser('find', 'role', 'textbox', 'fill', 'admin', '--name', 'Login', '--exact');
  await browser('find', 'role', 'textbox', 'fill', 'admin', '--name', 'Password', '--exact');
  await browser('click', 'input[type="submit"]');
  await browser('wait', 'a[href*="product/index.php"]');
  // Resolve the isolated product by its stable reference, without saving generated IDs.
  await browser('open', 'http://localhost:8000/product/card.php?ref=DISPATCH-LAMP');
  await browser('wait', 'a[href*="/product/stock/product.php"]');
  await browser('find', 'role', 'link', 'click', '--name', 'Stock', '--exact');
  // Verified stock surface: http://localhost:8000/product/stock/product.php
  await browser('wait', '--text', 'Physical Stock');
  await browser('wait', 'a[href*="movement_list.php?idproduct="]');
}
