import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => (await exec('agent-browser', args)).stdout;
const validation = '[aria-label="Summary"] button[title="Configure validation"]';
const visibility = '[aria-label="Summary"] button[title="Configure visibility"]';
const summary = '[aria-label="Summary"]';
const validationCount = `${summary} [data-glpi-editor-validation-conditions-count-badge]`;
const visibilityCount = `${summary} [data-glpi-editor-visibility-conditions-count-badge]`;
const validationCondition = `${summary} [data-testid="validation-condition"]`;

async function reportCounts(stage) {
  console.log(JSON.stringify({ stage,
    validation: (await browser('get', 'text', validationCount)).trim(),
    visibility: (await browser('get', 'text', visibilityCount)).trim(),
  }));
}

async function readValidation() {
  return {
    count: (await browser('get', 'count', validationCondition)).trim(),
    operator: (await browser('get', 'value', `${validationCondition} select[data-glpi-conditions-editor-value-operator]`)).trim(),
    value: (await browser('get', 'value', `${validationCondition} input[type="number"]`)).trim(),
    item: (await browser('get', 'value', `${validationCondition} input[data-glpi-conditions-editor-item]`)).trim(),
  };
}

export default async function action() {
  // 1. Present the existing question and its two count badges.
  await browser('wait', '1800');
  await reportCounts('given');
  if ((await browser('get', 'text', validationCount)).trim() !== '1'
      || (await browser('get', 'text', visibilityCount)).trim() !== '1') {
    throw new Error('Given requires both Summary count badges to display 1');
  }

  // 2. Inspect the configured validation criterion without editing it.
  await browser('click', validation);
  await browser('wait', '[aria-label="Summary"] [data-testid="validation-condition"] input[type="number"]');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '1800');
  const originalValidation = await readValidation();
  console.log(JSON.stringify({ stage: 'validation-inspected', ...originalValidation }));
  console.log(await browser('snapshot', '-s', summary));
  if (originalValidation.count !== '1' || originalValidation.operator !== 'length_greater_than'
      || originalValidation.value !== '5') {
    throw new Error('Given requires one length-greater-than-5 validation criterion');
  }

  // 3. Switch to the visibility editor and inspect its configured criterion.
  await browser('click', validation);
  await browser('click', visibility);
  await browser('wait', '[aria-label="Summary"] [data-testid="visibility-dropdown"] input[value="Assistance"]');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '1800');
  console.log(await browser('snapshot', '-s', summary));

  // 4. Remove only the visibility criterion and expose both resulting badges.
  await browser('click', '[aria-label="Summary"] [data-testid="visibility-dropdown"] [data-glpi-condition-editor-delete-condition]');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '1200');
  await browser('click', visibility);
  await browser('wait', '2200');
  await reportCounts('after-visibility-editor-closed');
  console.log(await browser('snapshot', '-s', summary));
  // Read the remaining form controls as diagnostics; no state is changed.
  const remainingValidation = await readValidation();
  console.log(JSON.stringify({ stage: 'validation-after-deletion', ...remainingValidation,
    unchanged: JSON.stringify(remainingValidation) === JSON.stringify(originalValidation),
  }));
}
