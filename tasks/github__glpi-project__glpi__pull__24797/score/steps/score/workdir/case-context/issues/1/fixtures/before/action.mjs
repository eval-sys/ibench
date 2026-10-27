import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => (await exec('agent-browser', args)).stdout;
const validation = '[aria-label="Summary"] button[title="Configure validation"]';
const visibility = '[aria-label="Summary"] button[title="Configure visibility"]';

export default async function action() {
  // 1. Present the existing question and its two count badges.
  await browser('wait', '1800');

  // 2. Inspect the configured validation criterion without editing it.
  await browser('click', validation);
  await browser('wait', '[aria-label="Summary"] [data-testid="validation-condition"] input[type="number"]');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '1800');

  // 3. Switch to the visibility editor and inspect its configured criterion.
  await browser('click', validation);
  await browser('click', visibility);
  await browser('wait', '[aria-label="Summary"] [data-testid="visibility-dropdown"] input[value="Assistance"]');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '1800');

  // 4. Remove only the visibility criterion and expose both resulting badges.
  await browser('click', '[aria-label="Summary"] [data-testid="visibility-dropdown"] [data-glpi-condition-editor-delete-condition]');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '1200');
  await browser('click', visibility);
  await browser('wait', '2200');
}
