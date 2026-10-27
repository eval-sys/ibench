import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
  return stdout;
}

export default async function setup() {
  const appURL = process.env.APP_URL.replace(/\/$/, '');
  await browser('open', `${appURL}/login`);
  await browser('wait', '#login-account-name');
  await browser('fill', '#login-account-name', 'morgan_review@example.com');
  await browser('fill', '#login-account-password', 'ReviewPass!2026');
  await browser('click', '#login-button');
  await browser('wait', 'a.sidebar-section-link[data-link-name="review"]');
  await browser('click', 'a.sidebar-section-link[data-link-name="review"]');
  await browser('wait', '--url', `${appURL}/review?sort_order=score`);
  await browser('wait', '.review-item:has(.review-item__meta-flagged-user a[data-user-card="casey_review"]) .reviewable-action-dropdown');
  await browser('wait', '.review-item:has(.review-item__meta-flagged-user a[data-user-card="casey_review"]) .timeline-event');
  // Present the post, penalty icon and initial timeline together at the desktop size.
  await browser('wait', '500');
}
