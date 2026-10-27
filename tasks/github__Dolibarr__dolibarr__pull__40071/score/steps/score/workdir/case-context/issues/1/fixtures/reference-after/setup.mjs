import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
async function browser(...args) {
  const result = await exec('agent-browser', args, { timeout: 60000, maxBuffer: 1024 * 1024 });
  return result.stdout;
}

export default async function setup() {
  // /opt/dev-env-profile.sh loads dev/initdemo/mysqldump_dolibarr_24.0.0.sql.
  // Its stable draft FI1007-0002 contains the Pres line; admin/admin is the
  // shipped login documented in dev/initdemo/README.md and verified here.
  // Endpoint is established by the environment profile and htdocs/conf/conf.php.
  const appURL = process.env.APP_URL || 'http://localhost:8000/';
  await browser('open', appURL);
  await browser('wait', '#username');
  await browser('fill', '#username', 'admin');
  await browser('fill', '#password', 'admin');
  await browser('find', 'role', 'button', 'click', '--name', ' Login ', '--exact');
  await browser('wait', 'a[href*="mainmenu=commercial"]');

  // Verified navigation: http://localhost:8000/comm/index.php?mainmenu=commercial&leftmenu=
  await browser('find', 'role', 'link', 'click', '--name', 'Commerce', '--exact');
  await browser('wait', '--url', '**/comm/index.php?mainmenu=commercial&leftmenu=');
  await browser('wait', 'a[href*="/fichinter/card.php?id="]');
  // Verified demo destination: http://localhost:8000/fichinter/card.php?id=2
  // Follow the reference link so the app resolves the prepared record, rather
  // than relying on a generated database identifier or a saved session token.
  await browser('find', 'role', 'link', 'click', '--name', ' FI1007-0002', '--exact');
  await browser('wait', 'a.editfielda[href*="action=editline"]');
  await browser('wait', '#cke_np_desc iframe');
  await browser('wait', '.tabsAction a.butActionDelete');
  const cardText = await browser('get', 'text', 'body');
  for (const text of ['FI1007-0002', 'Indian SAS', 'Draft', 'Pres']) {
    if (!cardText.includes(text)) throw new Error(`Missing starting state: ${text}`);
  }
  for (const command of ['validate', 'clone', 'delete']) {
    const selector = `.tabsAction a[href*="action=${command}"]`;
    if (!(await browser('is', 'enabled', selector)).trim().endsWith('true')) {
      throw new Error(`Starting record command is unavailable: ${command}`);
    }
  }
  await browser('scroll', 'up', '2000');
}
