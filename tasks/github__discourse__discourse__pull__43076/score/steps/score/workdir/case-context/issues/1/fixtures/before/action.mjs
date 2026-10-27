import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
  return stdout;
}

const item = '.review-item:has(.review-item__meta-flagged-user a[data-user-card="casey_review"])';
export default async function action() {
  // Step 1: the pending review and initial timeline are already loaded.
  await browser('scroll', 'down', '60');
  await browser('wait', '3000');

  // Step 2: inspect the author's pre-existing silence through the visible user link.
  await browser('click', `${item} .review-item__meta-flagged-user .names a`);
  await browser('wait', '#user-card .silence-reason');
  await browser('wait', '3000');

  // Step 3: open the agreeing actions on this same review item.
  await browser('click', `${item} .review-item__aside-title`);
  await browser('click', `${item} .reviewable-action-dropdown summary[data-name="Yes"]`);
  await browser('wait', `${item} [role="menuitemradio"][data-name="Delete post"]`);
  await browser('wait', '3000');

  // Step 4: delete the flagged post and inspect the resulting review timeline.
  await browser('click', `${item} [role="menuitemradio"][data-name="Delete post"]`);
  await browser('wait', '--text', 'Post deleted by');
  await browser('wait', '--text', 'Approved by');
  await browser('scroll', 'down', '120');
  await browser('wait', '1800');
}
