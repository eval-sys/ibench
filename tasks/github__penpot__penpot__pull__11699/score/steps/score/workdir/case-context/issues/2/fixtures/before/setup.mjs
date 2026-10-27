import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const run = async (...args) => {
  const { stdout } = await execFileAsync('agent-browser', args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  return stdout.trim();
};

export default async function setup() {
  await run('open', 'http://localhost:3000/#/auth/login');
  await run('wait', 'input[type="email"]');
  await run('find', 'label', 'Work email', 'fill', 'inspect.editor.11699@example.com');
  await run('find', 'label', 'Password', 'fill', 'WorkspacePass123!');
  await run('find', 'role', 'button', 'click', '--name', 'CONTINUE');
  await run('wait', '[data-testid="dashboard-files-layout-list"]');
  await run('click', '[data-testid="dashboard-files-layout-list"]');
  await run('wait', '[role="button"][aria-label="Inspect Save Study"]');
  await run('dblclick', '[role="button"][aria-label="Inspect Save Study"]');
  await run('wait', 'button[aria-label="Rectangle (R)"]');
}
