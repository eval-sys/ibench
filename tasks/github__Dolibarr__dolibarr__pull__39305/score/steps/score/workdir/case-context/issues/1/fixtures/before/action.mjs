import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
export default async function action() {
  // Step 1: present the existing free-text lines, costs, and 20% mark rates.
  await browser('wait', '1800');
  // Step 2: use the mark-rate column's visible edit control and enter 25%.
  await browser('click', 'a:has(.clickmarkforalllines)');
  await browser('wait', 'input[name="markforalllines"]');
  await browser('fill', 'input[name="markforalllines"]', '25');
  await browser('wait', '1200');
  // Step 3: submit; scroll the wide table into view alongside the error toast.
  await browser('click', 'input[name="submitforallmark"]');
  await browser('wait', '--load', 'networkidle');
  await browser('scroll', 'down', '380');
  await browser('scroll', 'right', '280');
  await browser('wait', '1800');
}
