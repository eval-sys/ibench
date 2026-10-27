import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);

export default async function cleanup() {
  // The trusted driver may invoke cleanup on about:blank, which has no web storage.
  const { stdout } = await exec('agent-browser', ['get', 'url'], { timeout: 60000 });
  if (stdout.trim().startsWith('https://localhost:9200/')) {
    await exec('agent-browser', ['storage', 'local', 'clear'], { timeout: 60000 });
    await exec('agent-browser', ['storage', 'session', 'clear'], { timeout: 60000 });
  }
  await exec('agent-browser', ['cookies', 'clear'], { timeout: 60000 });
  // cleanup.sh owns server-side document removal.
}
