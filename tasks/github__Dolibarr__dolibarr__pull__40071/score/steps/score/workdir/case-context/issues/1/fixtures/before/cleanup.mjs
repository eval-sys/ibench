import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
async function browser(...args) {
  const result = await exec('agent-browser', args, { timeout: 60000, maxBuffer: 1024 * 1024 });
  return result.stdout;
}

export default async function cleanup() {
  // The interaction never submits edits or changes a prepared record.
  // Only this disposable browser context's authentication cookies need clearing.
  await browser('cookies', 'clear');
}
