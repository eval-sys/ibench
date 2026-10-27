import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => {
  const { stdout } = await exec('agent-browser', args, { timeout: 30000 });
  if (stdout) process.stdout.write(stdout);
};

export default async function action() {
  await browser('click', '.branch-dropdown-button');
  await browser('wait', '.branch-selector-dropdown .menu.visible .item.selected');
  await browser('wait', '1200');

  await browser('hover', '.branch-tag-item.active');
  await browser('wait', '1200');

  await browser('click', '.branch-tag-item.active');
  await browser('wait', '1500');
}
