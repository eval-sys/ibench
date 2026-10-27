import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => {
  const {stdout} = await exec('agent-browser', args, {timeout: 60000});
  if (stdout) process.stdout.write(stdout);
};

export default async function action() {
  // Step 1: present the existing selection before its causal batch action.
  await browser('wait', '1800');

  // Step 2: the genuine dependency rejection comes from Gitea, without interception.
  await browser('find', 'role', 'button', 'click', '--name', 'Close', '--exact');
  await browser('wait', '.toastify.on');
  await browser('wait', '1800');
  await browser('snapshot');
  await browser('network', 'requests', '--filter', '/issues/status');
}
