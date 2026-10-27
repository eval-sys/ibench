import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 30000 });
const appURL = (process.env.APP_URL || 'http://localhost:3000').replace(/\/$/, '');

export default async function setup() {
  await browser('open', `${appURL}/user/login`);
  await browser('wait', '#user_name');
  await browser('fill', '#user_name', 'casey');
  await browser('fill', '#password', 'RiverStone!482');
  await browser('find', 'role', 'button', 'click', '--name', 'Sign In');
  await browser('wait', '--fn', `location.href === ${JSON.stringify(`${appURL}/`)} && !!document.querySelector("a[href='/user/settings']")`);
  await browser('find', 'role', 'menu', 'click', '--name', 'Profile and Settings…');
  await browser('click', 'a[href="/user/settings"]');
  await browser('wait', '--url', `${appURL}/user/settings`);
  await browser('click', '.flex-container-nav details summary');
  await browser('click', 'a[href="/user/settings/actions/secrets"]');
  await browser('wait', '--url', `${appURL}/user/settings/actions/secrets`);
  await browser('wait', '.show-modal[data-modal="#add-secret-modal"]');
  await browser('click', '.show-modal[data-modal="#add-secret-modal"]');
  await browser('wait', '#add-secret-modal.active.visible:not(.animating)');
}
