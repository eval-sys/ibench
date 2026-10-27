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

  // 3. Only after the initial typing, inspect ordinary keyboard navigation.
  // Read-only inventory includes enabled controls even if a regression removes
  // them from the Tab order. The bound limits diagnostics, not valid layouts.
  const controls = `(() => {
    const modal = document.querySelector('.oppia-feedback-modal');
    const items = [...modal.querySelectorAll('button,input:not([type="hidden"]),select,textarea,a[href],[role="button"],[tabindex]')]
      .filter(el => !el.disabled && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
    return {items: items.map((el, index) => ({index, tag: el.tagName,
      type: el.type || null, label: el.getAttribute('aria-label') || el.labels?.[0]?.textContent.trim() || el.textContent.trim(),
      classes: el.className, tabIndex: el.tabIndex})),
      focused: items.indexOf(document.activeElement),
      focusedDescription: document.activeElement === modal.querySelector('textarea')};
  })()`;
  console.log('Available modal controls:', await browser('eval', controls));
  const reached = new Set();
  for (let step = 1; step <= 24; step += 1) {
    await browser('press', 'Tab');
    await browser('wait', '650');
    const state = JSON.parse(await browser('eval', controls));
    if (state.focused >= 0) reached.add(state.focused);
    console.log('Keyboard focus:', JSON.stringify({step, focused: state.focused,
      control: state.items[state.focused] || null,
      focusedDescription: state.focusedDescription}));
    if (state.focusedDescription) {
      break;
    }
  }
  const finalState = JSON.parse(await browser('eval', controls));
  console.log('Keyboard traversal:', JSON.stringify({reached: [...reached],
    unreached: finalState.items.filter(item => !reached.has(item.index))}));
  await browser('snapshot', '-i');
}
