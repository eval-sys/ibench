import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const run = promisify(execFile);
async function browser(...args) {
  const { stdout } = await run('agent-browser', ['--json', ...args], { timeout: 60000, maxBuffer: 1048576 });
  const result = JSON.parse(stdout);
  if (!result.success) throw new Error(result.error || stdout);
  return result.data;
}

export default async function setup() {
  const appUrl = process.env.APP_URL || 'http://localhost:8000';
  // Credentials are fixed by config-defaults.php and the environment's native installer.
  await browser('open', new URL('/index.php/admin/authentication/sa/login', appUrl).href);
  await browser('find', 'label', 'Username', 'fill', 'admin');
  await browser('find', 'label', 'Password', 'fill', 'password');
  await browser('find', 'role', 'button', 'click', '--name', 'Log in', '--exact');
  await browser('wait', '--text', 'Surveys');
  await browser('wait', '--load', 'networkidle');
  await browser('open', new URL('/index.php/admin/emailtemplates/sa/index/surveyid/425401', appUrl).href);
  await browser('wait', '--text', "There are errors with this template's attachments. Please check them below.");
  await browser('wait', '--load', 'networkidle');
  await browser('scroll', 'up', '2000', '--selector', 'html');
}
