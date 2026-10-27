import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = async (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function action() {
  // Step 1: the loaded list exposes the company/building/room parent links.
  const { stdout } = await browser('tab', 'list', '--json');
  const tab = JSON.parse(stdout).data.tabs.find(t => t.active).tabId;
  // In agent-browser 0.33, reselecting the current tab after navigation
  // keeps the recorder capturing it. This focuses the same tab without reload.
  await browser('tab', tab);
  await browser('wait', '2500');

  // Step 2: open the room through its visible name.
  await browser('find', 'role', 'link', 'click', '--name', 'Room 101', '--exact');
  await browser('wait', '#parent a');
  await browser('wait', '--load', 'networkidle');
  await browser('tab', tab);
  await browser('wait', '2500');

  // Step 3: follow the immediate parent in the right-hand panel.
  await browser('click', '#parent a');
  await browser('wait', '--fn', `document.querySelector('h1')?.innerText.includes('North Building')
    && document.querySelector('#parent a')?.innerText === 'Cedar Technologies'`);
  await browser('wait', '--load', 'networkidle');
  await browser('tab', tab);
  await browser('wait', '2500');

  // Step 4: return using browser history to inspect the same room again.
  await browser('back');
  await browser('wait', '--fn', `document.querySelector('h1')?.innerText.includes('Room 101')
    && document.querySelector('#parent a')?.innerText === 'North Building'`);
  await browser('wait', '--load', 'networkidle');
  await browser('tab', tab);
  await browser('wait', '2500');
}
