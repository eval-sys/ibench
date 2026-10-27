import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 30000 });

export default async function action() {
  // Step 1: present the existing email and password validation errors.
  await browser('wait', '1500');

  // Step 2: append the missing email portion while keeping the email focused.
  await browser('find', 'label', 'Email Address', 'click');
  await browser('press', 'End');
  await browser('keyboard', 'type', '@example.com');
  await browser('wait', '2000');

  // Step 3: moving to Password blurs the corrected email.
  await browser('find', 'label', 'Password', 'click');
  await browser('wait', '1500');

  // Step 4: replace the password with valid input and keep it focused.
  await browser('press', 'Control+a');
  await browser('keyboard', 'type', 'Kestrel!482');
  await browser('wait', '2500');
}
