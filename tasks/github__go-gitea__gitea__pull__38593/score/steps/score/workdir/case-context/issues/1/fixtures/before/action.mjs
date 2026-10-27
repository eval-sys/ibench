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
  await browser('wait', '--fn', 'document.querySelectorAll(".issue-checkbox").length === 3 && document.querySelectorAll(".issue-checkbox:checked").length === 0 && document.querySelector("#issue-filters").getBoundingClientRect().height > 0');
  await browser('wait', '1800');
}
