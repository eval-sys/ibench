import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 30000 });

export default async function action() {
  await browser('wait', '1400');
  await browser('fill', '#secret-name', '1DEPLOY_KEY');
  await browser('fill', '#secret-data', 'staging-access');
  await browser('wait', '1200');
  await browser('click', '#add-secret-modal .primary.ok.button');
  await browser('wait', '1200');
  await browser('hover', '#secret-name');
  await browser('wait', '700');
}
