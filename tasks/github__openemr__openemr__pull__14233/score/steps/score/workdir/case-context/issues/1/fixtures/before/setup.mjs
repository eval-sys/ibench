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
    // Bootstrap ignores dismissal while its opening transition is active.
    await browser('wait', '1000');
    await browser('find', 'role', 'button', 'click', '--name', 'Ask again later', '--exact');
    await browser('wait', '--fn', "!document.querySelector('.product-registration-modal.show') && !document.querySelector('.modal-backdrop')");
    return true;
  }
  return false;
}
export default async function setup() {
  const appURL = process.env.APP_URL || 'http://localhost:8000';
  await browser('open', new URL('/interface/login/login.php?site=default', appURL).href);
  await browser('fill', 'input[name=authUser]', 'admin');
  await browser('fill', 'input[name=clearPass]', 'pass');
  await browser('find', 'role', 'button', 'click', '--name', 'Login', '--exact');
  await browser('wait', '--url', '**/interface/main/tabs/main.php?token_main=*');
  await browser('wait', '3000');
  // The optional registration dialog arrives asynchronously. Settle it while
  // the original idle timeout is still in effect, before the measured pause.
  for (let i = 0; i < 30; i++) {
    if (await dismissRegistration()) break;
    await browser('wait', '1000');
  }
  await browser('wait', '--text', 'Calendar');
  console.log('Single authenticated Calendar is loaded before capture.');
  console.log('Browser tabs:', await browser('tab', 'list', '--json'));
  console.log('Initial main interface:', await browser('snapshot', '-i'));
  // A real Calendar operation starts the measured pause from recent activity.
  const day = Object.entries((await snapshot()).refs).find(([, r]) => r.role === 'link' && r.name === 'Day');
  if (!day) throw new Error('The initial authenticated Calendar has no Day control');
  await browser('click', '@' + day[0]);
  await browser('wait', '500');
  const { stdout } = await exec('bash', [new URL('./setup.sh', import.meta.url).pathname, 'enable']);
  console.log(stdout.trim());
}
