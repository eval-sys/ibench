import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec = promisify(execFile);
const browser = async (...args) => (await exec('agent-browser', args, {timeout: 60_000})).stdout;

export default async function action() {
  // 1. Present the already loaded Given, including the status tooltip.
  await browser('hover', '.run-list .item-leading span');
  await browser('wait', '1800');

  // 2. Follow the listed run and end it through its visible cancel control.
  await browser('click', '.run-list .item-title a');
  await browser('wait', 'button.tw-text-red');
  await browser('wait', '1000');
  await browser('find', 'role', 'button', 'click', '--name', 'Cancel workflow run');
  await browser('wait', '--text', 'Canceled');
  await browser('wait', '1800');

  // 3. Browser Back preserves the original list, unlike the repository's Actions link.
  await browser('back');
  await browser('wait', '.run-list .item-leading span');
  await browser('hover', '.run-list .item-leading span');
  await browser('wait', '15000');
  await browser('hover', '.run-list .item-leading span');
  await browser('wait', '1800');

}
