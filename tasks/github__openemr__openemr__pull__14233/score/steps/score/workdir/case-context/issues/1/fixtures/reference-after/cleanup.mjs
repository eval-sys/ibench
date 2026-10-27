import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
export default async function cleanup() {
  const browser = async (...args) => exec('agent-browser', args, { timeout: 60000 });
  // Native logout destroys only the session minted by this browser fixture.
  const appURL = process.env.APP_URL || 'http://localhost:8000';
  await browser('open', new URL('/interface/logout.php', appURL).href);
  await browser('wait', '--url', '**/login.php**');
  await browser('cookies', 'clear');
  await browser('storage', 'local', 'clear');
  await browser('storage', 'session', 'clear');
}
