import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const appURL = process.env.APP_URL || 'http://localhost:8000';
async function browser(...args) {
  return await exec('agent-browser', args, { timeout: 60000 });
}

export default async function action() {
  // Step 1: present the order list established by setup.
  await browser('wait', '2000');

  // Steps 2-5: the reported action is opening a wrong-id URL directly.
  // Use built-in navigation to preserve the exact requested IDs on all pages.
  const pages = [
    '/compta/prelevement/card.php?id=999999',
    '/compta/prelevement/fiche-rejet.php?id=999999',
    '/compta/prelevement/fiche-stat.php?id=999999',
    '/compta/prelevement/line.php?id=999999',
  ];
  for (const url of pages) {
    await browser('open', new URL(url, appURL).href);
    await browser('wait', '--load', 'networkidle');
    console.log(`Result for ${url}:`);
    console.log((await browser('snapshot', '-u')).stdout);
    // Hold each resulting page for visual inspection.
    await browser('wait', '2500');
  }
}
