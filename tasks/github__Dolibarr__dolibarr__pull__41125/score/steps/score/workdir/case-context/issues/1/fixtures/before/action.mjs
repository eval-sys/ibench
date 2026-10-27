import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
async function browser(...args) {
  await exec('agent-browser', args, { timeout: 60000 });
}

export default async function action() {
  // Step 1: present the order list established by setup.
  await browser('wait', '2000');

  // Steps 2-5: the reported action is opening a wrong-id URL directly.
  // The empty card's tab links use id= (not 999999), so clicking those tabs
  // would not exercise these missing-record requests. Use built-in navigation.
  const pages = [
    'http://localhost:8000/compta/prelevement/card.php?id=999999',
    'http://localhost:8000/compta/prelevement/fiche-rejet.php?id=999999',
    'http://localhost:8000/compta/prelevement/fiche-stat.php?id=999999',
    'http://localhost:8000/compta/prelevement/line.php?id=999999',
  ];
  for (const url of pages) {
    await browser('open', url);
    await browser('wait', '--load', 'networkidle');
    // Hold each resulting card for inspection, including the final line card.
    await browser('wait', '2500');
  }
}
