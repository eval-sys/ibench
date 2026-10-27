import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec = promisify(execFile);
const browser = async (...args) => (await exec('agent-browser', args, {timeout: 60_000})).stdout;

export default async function setup() {
  await browser('open', 'http://localhost:3001/user/login');
  await browser('wait', 'input[name="user_name"]');
  await browser('fill', 'input[name="user_name"]', 'morgan');
  await browser('fill', 'input[name="password"]', 'RiverStone47!');
  await browser('click', 'button.ui.primary.button');
  await browser('wait', 'a[href="/morgan/build-checks"]');
  await browser('find', 'first', 'a[href="/morgan/build-checks"]', 'click');
  await browser('wait', '--url', 'http://localhost:3001/morgan/build-checks');
  await browser('wait', 'a[href="/morgan/build-checks/actions"]');
  await browser('click', 'a[href="/morgan/build-checks/actions"]');
  await browser('wait', '--url', 'http://localhost:3001/morgan/build-checks/actions');
  await browser('wait', '.run-list .item-leading span[data-tooltip-content="Waiting"]');
}
