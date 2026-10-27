import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
  return stdout.trim();
}
export default async function cleanup() {
  const url = await browser('get', 'url');
  if (url.startsWith('http://localhost:8181/')) {
    await browser('storage', 'local', 'clear');
    await browser('storage', 'session', 'clear');
  }
  await browser('cookies', 'clear');
}
