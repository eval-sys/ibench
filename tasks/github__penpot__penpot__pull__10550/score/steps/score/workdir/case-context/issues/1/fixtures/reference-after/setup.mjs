import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const browser = (...args) =>
  execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });

export default async function setup() {
  const appURL = (process.env.APP_URL || 'http://localhost:3000').replace(/\/$/, '');
  await browser('open', `${appURL}/#/auth/login`);
  await browser('wait', '--text', 'Log into my account');
  await browser('find', 'label', 'Work email', 'fill', 'path.badge@example.com');
  await browser('find', 'label', 'Password', 'fill', 'PathBadge10550!');
  await browser('find', 'role', 'button', 'click', '--name', 'CONTINUE', '--exact');
  await browser('wait', '[role="button"][aria-label="Path Badge Canvas"]');

  let workspaceReady = false;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await browser('dblclick', '[role="button"][aria-label="Path Badge Canvas"]');
    await browser('wait', '1000');
    const { stdout } = await browser('get', 'url');
    if (stdout.includes('/#/workspace?')) {
      workspaceReady = true;
      break;
    }
  }
  if (!workspaceReady) throw new Error('The file card did not open the workspace');

  await browser('wait', '[data-testid="path-btn"]');
  await browser('wait', '--text', 'Page 1');
  await browser('wait', '2500');
  await browser('wait', '--fn', `document.querySelector('[data-testid="viewport"]')?.style.getPropertyValue('--zoom') === '1'`);
  console.log('Given: empty file at 100% zoom');
  console.log((await browser('snapshot')).stdout);
}
