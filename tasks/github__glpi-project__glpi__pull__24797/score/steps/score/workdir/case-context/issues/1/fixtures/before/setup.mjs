import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => (await exec('agent-browser', args)).stdout;

export default async function setup() {
  // Account and password are provided by install/empty_data.php.
  // Endpoint is established by /etc/apache2/sites-enabled/glpi.conf and
  // /opt/dev-env-profile.sh; the isolated form is created by setup.sh.
  await browser('open', 'http://localhost:8000/index.php');
  await browser('fill', 'input[name="login_name"]', 'glpi');
  await browser('fill', 'input[name="login_password"]', 'glpi');
  await browser('find', 'role', 'button', 'click', '--name', 'Sign in', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('open', 'http://localhost:8000/front/form/form.php');
  await browser('wait', '--load', 'networkidle');
  const snapshot = await browser('snapshot', '-i', '--json');
  const data = JSON.parse(snapshot);
  // Resolve the prepared form through its visible link, never a generated ID.
  // The installed browser ignored clicks after same-tab navigation during
  // investigation; opening the application's link in a new tab restored input.
  const refs = data.data?.refs ?? data.refs;
  const entry = Object.entries(refs).find(([, value]) =>
    value.role === 'link' && value.name === 'Service request details');
  if (!entry) throw new Error('Service request details link is missing');
  await browser('click', `@${entry[0]}`, '--new-tab');
  await browser('wait', 'input[value="Summary"]');
  await browser('wait', '--load', 'networkidle');
  await browser('click', 'input[value="Summary"]');
  await browser('wait', '[aria-label="Summary"] button[title="Configure validation"]');
  await browser('wait', '[aria-label="Summary"] button[title="Configure visibility"]');
}
