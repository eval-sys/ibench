import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, {timeout: 60000});
export default async function action() {
  // Step 1: Present the existing dashboard and its unselected Language field.
  await browser('wait', '1500');
  // Step 2: Use the native dropdown's type-ahead, then highlight English.
  await browser('click', 'select[aria-label="Select language"]');
  await browser('press', 'e');
  await browser('press', 'ArrowDown');
  await browser('wait', '1500');
  // Step 3: Confirm the highlighted option through the real keyboard path.
  await browser('press', 'Enter');
  await browser('wait', '1500');
}
