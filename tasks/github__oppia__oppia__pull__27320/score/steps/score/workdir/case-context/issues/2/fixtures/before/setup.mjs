import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
  return stdout.trim();
}
const appURL = process.env.APP_URL || 'http://localhost:8181';
export default async function setup() {
  await browser('open', `${appURL}/login?return_url=%2Fcommunity-library`);
  await browser('wait', '.e2e-test-sign-in-email-input');
  await browser('fill', '.e2e-test-sign-in-email-input', 'lesson.reader@example.com');
  await browser('click', '.e2e-test-sign-in-button');
  await browser('wait', '--url', `${appURL}/community-library`);
  // The fixture owns this lesson; enter its real public route directly.
  await browser('open', `${appURL}/explore/0`);
  await browser('wait', '--url', `${appURL}/lesson/0`);
  await browser('wait', '.e2e-test-player-sidebar-toggle');
  await browser('wait', '--text', "Incidentally, do you know where the name 'Oppia' comes from?");
  if ((await browser('snapshot', '-i')).includes('button "OK"')) {
    await browser('find', 'role', 'button', 'click', '--name', 'OK', '--exact');
  }
  await browser('wait', '500');
}
