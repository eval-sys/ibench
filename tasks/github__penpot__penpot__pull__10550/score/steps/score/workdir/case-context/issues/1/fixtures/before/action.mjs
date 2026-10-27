import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const browser = (...args) =>
  execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });

async function clickPoint(x, y) {
  await browser('mouse', 'move', String(x), String(y));
  await browser('mouse', 'down');
  await browser('mouse', 'up');
  await browser('wait', '250');
}

export default async function action() {
  await browser('wait', '800');
  await browser('mouse', 'move', '600', '350');
  await browser('wait', '200');
  await browser('click', '[data-testid="path-btn"]');
  await browser('wait', '[data-testid="path-btn"].main_ui_workspace_top_toolbar__selected');
  await browser('wait', '1000');

  await clickPoint(500, 250);
  await clickPoint(760, 260);
  await clickPoint(700, 460);
  await clickPoint(500, 250);
  await browser('wait', '1200');

  await browser('press', 'Escape');
  await browser('wait', '.selection-size-badge text');
  await browser('wait', '1200');
}
