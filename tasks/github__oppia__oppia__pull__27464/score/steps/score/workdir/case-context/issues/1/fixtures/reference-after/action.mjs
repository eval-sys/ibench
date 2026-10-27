import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, {timeout: 60000});

// Read-only diagnostics; all user input uses the browser's click/press commands.
const state = async label => {
  const {stdout} = await browser('eval', `JSON.stringify({
    language: document.querySelector('select[aria-label="Select language"]').value,
    label: document.querySelector('select[aria-label="Select language"]').selectedOptions[0]?.textContent.trim(),
    provider: document.querySelector('select[aria-label="Select provider"]').value,
    mappingRows: document.querySelectorAll('.e2e-test-mapping-row').length,
    automaticSuggestions: document.querySelector('.e2e-test-auto-translation-toggle input').checked,
    addDisabled: document.querySelector('.e2e-test-add-mapping-btn').disabled
  })`);
  console.log(label, stdout.trim());
  const decoded = JSON.parse(stdout);
  return typeof decoded === 'string' ? JSON.parse(decoded) : decoded;
};

export default async function action() {
  // Step 1: Establish the empty pending mapping and separate switch state.
  await browser('wait', '1500');
  const initial = await state('Given');
  if (initial.language !== '' || initial.provider !== '' ||
      initial.mappingRows !== 0 || initial.automaticSuggestions !== false ||
      initial.addDisabled !== true) {
    throw new Error('The required starting state is not established.');
  }
  // Step 2: Open the native chooser and highlight English with real keys.
  await browser('click', 'select[aria-label="Select language"]');
  await browser('press', 'e');
  await browser('press', 'ArrowDown');
  await browser('wait', '1500');
  // Step 3: Confirm through the keyboard path and observe without further input.
  await browser('press', 'Enter');
  await state('Immediately after Enter');
  await browser('wait', '1500');
  await state('After settling');
  await browser('wait', '2500');
  await state('Retained selection');
}
