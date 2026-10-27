import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
export default async function cleanup() {
  const { stdout } = await exec('agent-browser', ['get', 'url']);
  if (stdout.trim().startsWith('http://localhost:8000/')) {
    await exec('agent-browser', ['storage', 'local', 'clear']);
    await exec('agent-browser', ['storage', 'session', 'clear']);
  }
  await exec('agent-browser', ['cookies', 'clear']);
}
