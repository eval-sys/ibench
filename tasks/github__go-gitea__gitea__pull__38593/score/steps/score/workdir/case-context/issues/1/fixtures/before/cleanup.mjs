import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

const exec = promisify(execFile);

export default async function cleanup() {
  // Authentication cookies are the only browser-owned persistent fixture state.
  await exec('agent-browser', ['cookies', 'clear'], {timeout: 60000});
}
