import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
  return stdout.trim();
}
const appURL = process.env.APP_URL || 'http://localhost:8181';
export default async function setup() {
  await browser('open', `${appURL}/`);
  await browser('wait', '.e2e-test-report-website-issue-link');
  await browser('find', 'role', 'button', 'click', '--name', 'OK', '--exact');
  await browser('scrollintoview', '.e2e-test-report-website-issue-link');
  await browser('wait', '500');
}
