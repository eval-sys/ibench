import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);

export default async function cleanup() {
  await exec('agent-browser', ['cookies', 'clear'], { timeout: 30000 });
}
