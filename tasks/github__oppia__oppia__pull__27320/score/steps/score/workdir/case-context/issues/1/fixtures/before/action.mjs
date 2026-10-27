import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
  return stdout.trim();
}
export default async function action() {
  await browser('wait', '1100');
  // 1. Open the dialog from the home page footer and show the blank description.
  await browser('click', '.e2e-test-report-website-issue-link');
  await browser('wait', '.e2e-test-feedback-modal-textarea');
  await browser('wait', '1400');

  // Keep a non-default optional choice so preservation is observable.
  await browser('uncheck', '.e2e-test-technical-logs');

  // 2. Scroll the form to its lower controls, keeping the description blank.
  await browser('scroll', 'down', '600', '--selector', '.oppia-feedback-body');
  await browser('wait', '1400');

  console.log('Given:', await browser('eval', "JSON.stringify((() => {\n    const field = document.querySelector('.e2e-test-feedback-modal-textarea');\n    const body = document.querySelector('.oppia-feedback-body');\n    const f = field.getBoundingClientRect(), b = body.getBoundingClientRect();\n    const error = document.querySelector('.e2e-test-form-error');\n    const e = error?.getBoundingClientRect();\n    return {description: field.value, descriptionFullyAboveBody: f.bottom <= b.top,\n      descriptionVisible: f.top >= b.top && f.bottom <= b.bottom,\n      scrollTop: body.scrollTop, focusedDescription: document.activeElement === field,\n      error: error?.textContent.trim() || null,\n      errorVisible: !!e && e.top >= b.top && e.bottom <= b.bottom,\n      includeTechnicalLogs: document.querySelector('.e2e-test-technical-logs').checked,\n      screenshotPresent: !!document.querySelector('.e2e-test-feedback-screenshot-preview')};\n  })())"));

  // 3. Submit with the description off-screen and observe the validation response.
  await browser('click', '.e2e-test-confirm-action-button');
  await browser('wait', '1600');
  console.log('After Submit:', await browser('eval', "JSON.stringify((() => {\n    const field = document.querySelector('.e2e-test-feedback-modal-textarea');\n    const body = document.querySelector('.oppia-feedback-body');\n    const f = field.getBoundingClientRect(), b = body.getBoundingClientRect();\n    const error = document.querySelector('.e2e-test-form-error');\n    const e = error?.getBoundingClientRect();\n    return {description: field.value, descriptionFullyAboveBody: f.bottom <= b.top,\n      descriptionVisible: f.top >= b.top && f.bottom <= b.bottom,\n      scrollTop: body.scrollTop, focusedDescription: document.activeElement === field,\n      error: error?.textContent.trim() || null,\n      errorVisible: !!e && e.top >= b.top && e.bottom <= b.bottom,\n      includeTechnicalLogs: document.querySelector('.e2e-test-technical-logs').checked,\n      screenshotPresent: !!document.querySelector('.e2e-test-feedback-screenshot-preview')};\n  })())"));
  // 4. Only after observing the failed submission, inspect the warning above.
  await browser('scroll', 'up', '600', '--selector', '.oppia-feedback-body');
  await browser('wait', '1600');
}
