import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function setup() {
  // /opt/dev-env-profile.sh serves the UI on port 8080. Its pinned upstream
  // demo README documents admin/admin; do not create or reset an account.
  await browser('open', 'http://localhost:8080/login/');
  await browser('find', 'label', 'Username', 'fill', 'admin', '--exact');
  await browser('find', 'label', 'Password', 'fill', 'admin', '--exact');
  await browser('find', 'role', 'button', 'click', '--name', 'Sign In', '--exact');
  await browser('wait', '--url', 'http://localhost:8080/');
  await browser('wait', 'header [aria-label="Open user menu"]');
  // Show the catalog's distinct manufacturer values before opening the bay.
  await browser('open', 'http://localhost:8080/dcim/module-types/?q=SFP-25G');
  await browser('wait', '--text', 'Results 38');
  await browser('wait', 'a[href="/dcim/module-bay-types/"]');
}
