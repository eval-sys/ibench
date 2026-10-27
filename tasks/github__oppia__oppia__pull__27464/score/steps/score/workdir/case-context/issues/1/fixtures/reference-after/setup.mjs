import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, {timeout: 60000});
export default async function setup() {
  await browser('open', new URL('/contributor-admin-dashboard', process.env.APP_URL).href);
  await browser('wait', '--text', 'Enter an email');
  await browser('find', 'role', 'combobox', 'fill', '--name', 'Enter an email', 'language.manager@example.com');
  await browser('press', 'Tab');
  await browser('find', 'role', 'button', 'click', '--name', 'Sign In', '--exact');
  await browser('wait', '--url', '**/contributor-admin-dashboard');
  await browser('wait', '--text', 'Manage supported languages for auto-translation');
  await browser('wait', 'select[aria-label="Select language"]');
  // Dismiss the site's cookie notice through its visible control, if present.
  const {stdout} = await browser('snapshot', '-i');
  if (stdout.includes('button "OK"')) {
    await browser('find', 'role', 'button', 'click', '--name', 'OK', '--exact');
  }
}
