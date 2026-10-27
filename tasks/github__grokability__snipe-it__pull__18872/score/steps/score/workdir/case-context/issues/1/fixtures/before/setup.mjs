import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = async (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function setup() {
  // Endpoint: /opt/dev-env-profile.sh; credentials: UserSeeder + UserFactory.
  await browser('tab', 'new', 'http://localhost:8000/login');
  await browser('wait', 'input[name="username"]');
  await browser('find', 'role', 'textbox', 'fill', 'admin', '--name', 'Username');
  await browser('find', 'role', 'textbox', 'fill', 'password', '--name', 'Password');
  await browser('find', 'role', 'button', 'click', '--name', 'Login', '--exact');
  await browser('wait', '--url', 'http://localhost:8000/');
  await browser('wait', '--load', 'networkidle');
  await browser('open', 'http://localhost:8000/locations');
  await browser('wait', 'input.search-input');
  await browser('fill', 'input.search-input', 'Cedar campus directory');
  await browser('press', 'Enter');
  await browser('wait', '--fn', `(() => {
    const rows = [...document.querySelectorAll('#locationTable tbody tr')];
    return rows.length === 3 && rows.some(r => r.innerText.includes('Room 101') && r.innerText.includes('North Building'))
      && rows.some(r => r.innerText.includes('North Building') && r.innerText.includes('Cedar Technologies'));
  })()`);
}
