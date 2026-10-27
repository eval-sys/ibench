import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function action() {
  // Step 1: Present the document already opened by setup.
  // Read-only captures ensure the recorder samples each stable focus state.
  await browser('screenshot');
  await browser('wait', '1500');
  // Step 2: Navigate backwards from Close, through the context menu, to the filename.
  await browser('press', 'Shift+Tab');
  await browser('screenshot');
  await browser('wait', '600');
  await browser('press', 'Shift+Tab');
  await browser('screenshot');
  await browser('wait', '1500');
  // Step 3: Try to activate the focused filename and hold the resulting page.
  await browser('press', 'Enter');
  await browser('screenshot');
  await browser('wait', '1500');
}
