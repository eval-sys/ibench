import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
const appBase = (process.env.APP_URL || 'http://localhost:4533').replace(/\/$/, '');

export default async function cleanup() {
  // Browser authentication and column/drawer choices exist only in this clean session.
  const { stdout } = await browser('get', 'url');
  if (stdout.trim().startsWith(appBase + '/')) {
    await browser('storage', 'local', 'clear');
    await browser('storage', 'session', 'clear');
  }
  await browser('cookies', 'clear');
}
