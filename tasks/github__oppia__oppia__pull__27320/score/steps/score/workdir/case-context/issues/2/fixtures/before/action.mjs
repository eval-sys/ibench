import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
  return stdout.trim();
}
export default async function action() {
  await browser('wait', '1100');
  // 1. Reach the modal through the lesson's visible options drawer.
  await browser('click', '.e2e-test-player-sidebar-toggle');
  await browser('wait', '900');
  await browser('click', '.e2e-test-lesson-desktop-report-button');
  await browser('wait', '.e2e-test-feedback-modal-textarea');
  await browser('wait', '1500');

  console.log('New modal:', await browser('eval', "JSON.stringify({description: document.querySelector('.e2e-test-feedback-modal-textarea').value, counter: document.querySelector('.e2e-test-feedback-text-count').textContent.trim(), focusedDescription: document.activeElement === document.querySelector('.e2e-test-feedback-modal-textarea')})"));

  // 2. Send real keyboard input to the current focus without clicking the modal.
  await browser('keyboard', 'type', 'The image is missing.');
  await browser('wait', '1700');
  console.log('After initial typing:', await browser('eval', "JSON.stringify({description: document.querySelector('.e2e-test-feedback-modal-textarea').value, counter: document.querySelector('.e2e-test-feedback-text-count').textContent.trim(), focusedDescription: document.activeElement === document.querySelector('.e2e-test-feedback-modal-textarea')})"));

  // 3. Manually focus the description, then repeat the same input for comparison.
  await browser('click', '.e2e-test-feedback-modal-textarea');
  await browser('keyboard', 'type', 'The image is missing.');
  await browser('wait', '1700');
  console.log('After manual focus:', await browser('eval', "JSON.stringify({description: document.querySelector('.e2e-test-feedback-modal-textarea').value, counter: document.querySelector('.e2e-test-feedback-text-count').textContent.trim(), focusedDescription: document.activeElement === document.querySelector('.e2e-test-feedback-modal-textarea')})"));
}
