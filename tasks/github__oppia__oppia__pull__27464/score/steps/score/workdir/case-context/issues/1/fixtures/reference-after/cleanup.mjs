import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec = promisify(execFile);
export default async function cleanup() {
  // The trusted driver supplies a new browser for every run. This fixture
  // owns no browser storage beyond that disposable authenticated session.
  await exec('agent-browser', ['cookies', 'clear'], {timeout: 60000});
}
