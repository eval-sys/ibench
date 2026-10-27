import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);

export default async function cleanup() {
  // Only the browser authentication session is owned by this experiment.
  await exec('agent-browser', ['cookies', 'clear'], { timeout: 35000 });
}
