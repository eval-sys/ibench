import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const run = promisify(execFile);
async function browser(...args) {
  const { stdout } = await run('agent-browser', ['--json', ...args], { timeout: 60000, maxBuffer: 1048576 });
  const result = JSON.parse(stdout);
  if (!result.success) throw new Error(result.error || stdout);
  return result.data;
}

export default async function action() {
  // 1. Present the attachment warning already loaded by setup.
  await browser('wait', '1800');

  // 2. Inspect the configured missing file without saving or altering the template.
  await browser('scrollintoview', 'span.fa-exclamation-triangle[title="File not found."]');
  await browser('wait', '1800');

  // 3. Follow the survey's own Participants navigation and inspect its recipient.
  // Activate the real sidebar link with its keyboard interaction. Its mouse
  // click point is intermittently covered by the product's sticky toolbar.
  await browser('focus', '#sidemenu_participants');
  await browser('scroll', 'up', '200', '--selector', 'html');
  await browser('wait', '700');
  await browser('press', 'Enter');
  await browser('wait', '--text', 'alex.morgan@example.test');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--fn', "!document.querySelector('#pjaxClickInhibitor')");
  await browser('scroll', 'down', '280', '--selector', 'html');
  await browser('wait', '1800');

  // 4. Prepare the invitation using the visible menu; stop at the sending form.
  await browser('find', 'role', 'button', 'click', '--name', 'Invite & remind');
  await browser('wait', '700');
  await browser('find', 'role', 'menuitem', 'click', '--name', 'Send email invitation');
  await browser('wait', '--text', 'Send email invitations');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--fn', "!document.querySelector('#pjaxClickInhibitor')");
  await browser('scroll', 'up', '2000', '--selector', 'html');
  await browser('wait', '2200');
}
