import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
export default async function action() {
  // Present the already loaded physical-stock Given, then inspect its quantity field.
  await browser('wait', '2000');
  await browser('hover', 'input[name="tobuy0"]');
  await browser('wait', '2500');
}
