import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
async function browser(...args) {
  const result = await exec('agent-browser', args, { timeout: 60000, maxBuffer: 1024 * 1024 });
  return result.stdout;
}

export default async function action() {
  // Step 1: present the card already established by setup.
  await browser('wait', '1500');

  // Step 2: show the existing Pres line and the record action buttons together.
  await browser('scroll', 'down', '330');
  await browser('wait', '1500');

  // Step 3: use the visible pencil link, with the application's current token
  // and line identifier. Present the editor and retained record actions.
  await browser('click', 'a.editfielda[href*="action=editline"]');
  await browser('wait', 'input[name="save"]');
  await browser('wait', '#cke_np_desc iframe');
  await browser('scrollintoview', '.tabsAction');
  await browser('scroll', 'up', '170');
  await browser('wait', '2000');
}
