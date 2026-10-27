import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
async function browser(...args) {
  await exec('agent-browser', args, { timeout: 60000 });
}

export default async function setup() {
  // /opt/dev-env-profile.sh loads dev/initdemo/mysqldump_dolibarr_20.0.0.sql.
  // dev/initdemo/README.md documents the prepared admin/adminadmin login.
  await browser('open', 'http://localhost:8000/index.php');
  await browser('wait', 'input[name="username"]');
  await browser('fill', 'input[name="username"]', 'admin');
  await browser('fill', 'input[name="password"]', 'adminadmin');
  await browser('click', 'input[type="submit"]');
  await browser('wait', 'a[href="/compta/bank/list.php?mainmenu=bank&leftmenu=&search_status=opened"]');

  // Verified navigation destinations; follow the application's own menus.
  const bankURL = 'http://localhost:8000/compta/bank/list.php?mainmenu=bank&leftmenu=&search_status=opened';
  const debitURL = 'http://localhost:8000/compta/prelevement/index.php?leftmenu=withdraw&mainmenu=bank';
  const ordersURL = 'http://localhost:8000/compta/prelevement/orders_list.php?mainmenu=bank';
  for (const url of [bankURL, debitURL, ordersURL]) {
    const { pathname, search } = new URL(url);
    await browser('click', `a[href="${pathname}${search}"]`);
    await browser('wait', '--load', 'networkidle');
  }
  await browser('wait', 'a[href="/compta/prelevement/card.php?id=1&save_lastsearch_values=1"]');
}
