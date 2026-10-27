import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 60000, maxBuffer: 4 * 1024 * 1024 });
  return stdout.trim();
}
async function snapshot() {
  return JSON.parse(await browser('snapshot', '-i', '--json')).data;
}
async function dismissRegistration() {
  const snap = await snapshot();
  if (Object.values(snap.refs).some(r => r.name === 'Ask again later')) {
    await browser('find', 'role', 'button', 'click', '--name', 'Ask again later', '--exact');
  }
}
export default async function action() {
  const start = Date.now();
  const log = async label => console.log(`${label} at ${(Date.now() - start) / 1000}s:`, await browser('get', 'url'), await browser('snapshot', '-i'));
  await browser('network', 'requests', '--clear');
  await browser('console', '--clear');
  await log('Calendar before the idle pause');
  // Let ordinary idle expiration and two real 60-second reminder polls run.
  // Do not reload, log out, alter session timestamps, or invoke polling.
  for (let i = 0; i < 3; i++) {
    await browser('wait', '43000');
    await log('Idle calendar');
  }
  console.log('Natural requests:', await browser('network', 'requests'));
  console.log('Browser console:', await browser('console'));
  let snap = await snapshot();
  const week = Object.entries(snap.refs).find(([, r]) => r.role === 'link' && r.name === 'Week');
  if (week) {
    await browser('click', '@' + week[0]);
    await browser('wait', '2000');
    await log('After attempting Week');
  } else {
    await log('Week unavailable; inspect the visible recovery path');
  }
  console.log('Calendar requests:', await browser('network', 'requests', '--filter', '/interface/main/calendar/'));
  snap = await snapshot();
  if (Object.values(snap.refs).some(r => r.role === 'button' && r.name === 'Login')) {
    console.log(`Submit genuine credentials at ${(Date.now() - start) / 1000}s.`);
    await browser('fill', 'input[name=authUser]', 'admin');
    await browser('fill', 'input[name=clearPass]', 'pass');
    await browser('find', 'role', 'button', 'click', '--name', 'Login', '--exact');
    await browser('wait', '--url', '**/interface/main/tabs/main.php?token_main=*');
    await browser('wait', '2000');
    await dismissRegistration();
    await browser('wait', '--text', 'Calendar');
    await log('Calendar resumed after genuine authentication');
  }
  await browser('wait', '2000');
}
