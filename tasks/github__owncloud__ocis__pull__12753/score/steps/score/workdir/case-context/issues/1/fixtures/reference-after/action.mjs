import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });

// Read-only diagnostics: key input itself always uses the built-in press command.
async function recordFocus(label) {
  const { stdout } = await browser('eval', `JSON.stringify({
    focused: {tag: document.activeElement.tagName, id: document.activeElement.id,
      label: document.activeElement.getAttribute('aria-label'),
      text: document.activeElement.textContent.trim(),
      outline: getComputedStyle(document.activeElement).outline},
    filename: document.querySelector('#app-top-bar-resource')?.textContent.trim(),
    url: location.href
  })`);
  console.log(label, stdout.trim());
}

export default async function action() {
  // Step 1: Present the document already opened by setup.
  // Read-only captures ensure the recorder samples each stable focus state.
  await browser('screenshot');
  await recordFocus('Starting focus');
  await browser('wait', '1500');
  // Step 2: Navigate backwards twice from Close.
  await browser('press', 'Shift+Tab');
  await browser('screenshot');
  await recordFocus('After first Shift+Tab');
  await browser('wait', '600');
  await browser('press', 'Shift+Tab');
  await browser('screenshot');
  await recordFocus('After second Shift+Tab');
  await browser('wait', '1500');
  // Step 3: Activate whichever control keyboard traversal actually reached.
  await browser('press', 'Enter');
  await browser('screenshot');
  await recordFocus('After Enter');
  await browser('wait', '1500');
}
