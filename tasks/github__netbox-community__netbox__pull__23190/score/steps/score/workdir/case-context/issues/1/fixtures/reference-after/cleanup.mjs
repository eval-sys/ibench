import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);

export default async function cleanup() {
  // No custom browser storage is used. Remove the normal authentication cookie.
  await exec('agent-browser', ['cookies', 'clear'], { timeout: 60000 });
}
