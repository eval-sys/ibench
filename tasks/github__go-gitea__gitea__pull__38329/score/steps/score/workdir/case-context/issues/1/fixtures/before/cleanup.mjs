import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec = promisify(execFile);
const browser = async (...args) => (await exec('agent-browser', args, {timeout: 60_000})).stdout;

export default async function cleanup() {
  await browser('cookies', 'clear');
}
