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

const fileSelector = '[role="button"][aria-label="Inspect Save Study"]';

export default async function action() {
  await run('click', 'button[aria-label="Rectangle (R)"]');
  await run('wait', '1000');
  await run('mouse', 'move', '500', '190');
  await run('mouse', 'down');
  await run('mouse', 'move', '650', '300');
  await run('mouse', 'up');
  await run('wait', '1300');
  await run('wait', '[title="Saving"]');
  await run('hover', '[title="Saving"]');
  await run('wait', '500');

  await run('find', 'role', 'tab', 'click', '--name', 'INSPECT');
  await run('wait', '--text', 'Inspecting code (View Only)');
  await run('wait', '3800');

  await run('click', 'a[class*="main-icon"]');
  await run('wait', '[data-testid="dashboard-files-layout-list"]');
  await run('click', '[data-testid="dashboard-files-layout-list"]');
  await run('wait', fileSelector);
  await run('dblclick', fileSelector);
  await run('wait', 'button[aria-label="Rectangle (R)"]');
  await run('wait', '1200');
}
