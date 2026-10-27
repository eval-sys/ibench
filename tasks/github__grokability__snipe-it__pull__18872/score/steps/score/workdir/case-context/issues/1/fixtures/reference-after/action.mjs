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
  console.log('LOCATIONS LIST\n' + (await browser('snapshot', '-s', '#locationTable')).stdout);

  // Step 2: open the room through its visible name.
  await browser('find', 'role', 'link', 'click', '--name', 'Room 101', '--exact');
  await browser('wait', '#parent a');
  await browser('wait', '--load', 'networkidle');
  await browser('tab', tab);
  // Hover the visible link so the recording receives a fresh painted frame.
  await browser('hover', '#parent a:last-child');
  await browser('wait', '2500');
  console.log('ROOM BEFORE PARENT VISIT\n' + (await browser('snapshot', '-u')).stdout);

  // Step 3: follow the immediate parent in the right-hand panel.
  const parentPanel = (await browser('snapshot', '-i', '-s', '#parent')).stdout;
  const northBuilding = parentPanel.match(/link "North Building" \[ref=(e\d+)\]/);
  if (!northBuilding) throw new Error('North Building navigation target missing from Parent panel');
  await browser('click', `@${northBuilding[1]}`);
  await browser('wait', '--fn', `document.querySelector('h1')?.innerText.includes('North Building')
    && document.querySelector('#parent a')?.innerText === 'Cedar Technologies'`);
  await browser('wait', '--load', 'networkidle');
  await browser('tab', tab);
  await browser('hover', '#parent a:last-child');
  await browser('wait', '2500');
  console.log('BUILDING\n' + (await browser('snapshot', '-u')).stdout);

  // Step 4: return using browser history to inspect the same room again.
  await browser('back');
  await browser('wait', '--fn', `document.querySelector('h1')?.innerText.includes('Room 101')`);
  await browser('wait', '--load', 'networkidle');
  await browser('tab', tab);
  await browser('hover', '#parent a:last-child');
  await browser('wait', '2500');
  console.log('ROOM AFTER BACK\n' + (await browser('snapshot', '-u')).stdout);
}
