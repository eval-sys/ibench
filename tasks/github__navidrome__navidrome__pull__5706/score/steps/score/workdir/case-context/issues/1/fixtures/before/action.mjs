import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function action() {
  // Step 1: Present the existing title order and enabled Composer header.
  await browser('wait', 'thead [data-sort="composer"]');
  await browser('wait', '1500');

  // Step 2: Use the visible column control, then present its returned rows.
  await browser('find', 'role', 'button', 'click', '--name', 'Composer', '--exact');
  await browser('wait', '--fn', `document.querySelector('[data-sort="composer"].MuiTableSortLabel-active .MuiTableSortLabel-iconDirectionAsc') !== null &&
    document.querySelectorAll('tbody tr').length === 4 &&
    document.querySelector('[role="progressbar"]') === null`);
  await browser('find', 'role', 'heading', 'hover', '--name', 'Navidrome - Songs', '--exact');
  await browser('wait', '1800');
}
