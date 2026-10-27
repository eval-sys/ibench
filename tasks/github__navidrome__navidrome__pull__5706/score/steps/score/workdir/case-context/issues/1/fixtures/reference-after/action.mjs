import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function action() {
  // Inspect the displayed header, whether sortable or plain, and initial rows.
  console.log((await browser('snapshot')).stdout);
  await browser('find', 'role', 'columnheader', 'text', '--name', 'Composer', '--exact');
  await browser('wait', '1500');

  // A native browser click on the visible header is the user's sort attempt.
  await browser('find', 'role', 'columnheader', 'click', '--name', 'Composer', '--exact');
  await browser('wait', '--fn', `document.querySelectorAll('tbody tr').length === 4 &&
    document.querySelector('[role="progressbar"]') === null`);
  await browser('find', 'role', 'heading', 'hover', '--name', 'Navidrome - Songs', '--exact');
  await browser('wait', '1800');
  console.log((await browser('snapshot')).stdout);
  // Read-only diagnostics; no sort state or events are injected.
  console.log((await browser('eval', `JSON.stringify({
    headers: Array.from(document.querySelectorAll('thead th')).map(e => ({text:e.textContent, html:e.innerHTML})),
    rows: Array.from(document.querySelectorAll('tbody tr')).map(e => e.innerText)
  })`)).stdout);
}
