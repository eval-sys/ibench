import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 35000 });

export default async function action() {
  // Step 1: Present the existing Display page and current theme.
  await browser('wait', '1500');

  // Step 2: Follow the visible admin navigation to the password confirmation.
  await browser('scrollintoview', '#aside_feed a[href$="?c=user&a=manage"]');
  await browser('find', 'role', 'link', 'click', '--name', 'Manage users', '--exact');
  await browser('wait', '--text', 'Reauthentication is required');
  await browser('wait', '1200');

  // Step 3: Complete the prompt; leave every Create new user field untouched.
  await browser('fill', '#passwordPlain', 'profile-development');
  await browser('wait', 'button[type="submit"]:not([disabled])');
  await browser('wait', '800');
  await browser('find', 'role', 'button', 'click', '--name', 'Login', '--exact');
  await browser('wait', '#new_user_name');
  await browser('wait', '2500');
}
