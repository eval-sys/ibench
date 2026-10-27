import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
export default async function cleanup() {
  const { stdout } = await exec('agent-browser', ['get', 'url']);
  const appURL = (process.env.APP_URL || 'http://localhost:8000').replace(/\/$/, '');
  if (stdout.trim().startsWith(`${appURL}/`)) {
    await exec('agent-browser', ['storage', 'local', 'clear']);
    await exec('agent-browser', ['storage', 'session', 'clear']);
  }
  await exec('agent-browser', ['cookies', 'clear']);
}
