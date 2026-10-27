import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
async function browser(...args) {
  return exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
}

export default async function action() {
  // 1. Present the two already loaded interface records.
  await browser('wait', '1500');

  // 2. Follow the visible record link; the Connection panel fits at desktop size.
  // The native interface list sorts the two names in device order (A, then B).
  await browser('click', 'tbody tr:first-child td:nth-child(2) a');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--text', 'Not Connected');
  await browser('wait', '2000');

  // 3. Review the real changelog, including related termination entries.
  await browser('find', 'role', 'link', 'click', '--name', 'Changelog', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', 'table');
  await browser('wait', '2500');

  // 4. Open the latest update to the interface, rather than the related
  // termination deletion, and present the recorded cable field difference.
  await browser('find', 'first', 'tbody tr:has(.text-bg-blue):has(a[href^="/dcim/interfaces/"]) td:first-child a', 'click');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--text', 'Post-Change Data');
  await browser('wait', '2500');
}
