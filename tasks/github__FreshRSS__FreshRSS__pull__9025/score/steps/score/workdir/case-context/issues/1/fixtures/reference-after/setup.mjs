import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 35000 });

export default async function setup() {
  const appURL = process.env.APP_URL || 'http://localhost:3210';
  // The environment profile provisions admin with this password and the default Origine theme.
  await browser('open', `${appURL}/i/`);
  await browser('wait', '#username');
  await browser('fill', '#username', 'admin');
  await browser('fill', '#passwordPlain', 'profile-development');
  await browser('wait', '#loginButton:not([disabled])');
  await browser('click', '#loginButton');
  await browser('wait', 'a[href*="#dropdown-configure"]');
  await browser('click', 'a[href*="#dropdown-configure"]');
  await browser('find', 'role', 'link', 'click', '--name', 'Display', '--exact');
  await browser('wait', '--url', `${appURL}/i/?c=configure&a=display`);
  await browser('wait', '#aside_feed a[href$="?c=user&a=manage"]');
  await browser('wait', '--fn', "document.querySelector('#theme').value === 'Origine'");
}
