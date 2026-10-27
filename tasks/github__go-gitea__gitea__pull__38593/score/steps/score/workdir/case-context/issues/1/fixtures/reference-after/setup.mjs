import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

const exec = promisify(execFile);
const appUrl = (process.env.APP_URL || 'http://localhost:3000').replace(/\/$/, '');
const browser = async (...args) => {
  const {stdout} = await exec('agent-browser', args, {timeout: 60000});
  if (stdout) process.stdout.write(stdout);
};

export default async function setup() {
  // Endpoint documented by /opt/dev-env-profile.sh. Follow the product's links
  // after authentication, retaining the same browser document/session path.
  await browser('open', `${appUrl}/user/login`);
  await browser('fill', '#user_name', 'release-coordinator');
  await browser('fill', '#password', 'ReleasePlan42!');
  await browser('find', 'role', 'button', 'click', '--name', 'Sign In', '--exact');
  await browser('wait', 'a[href="/release-coordinator/release-planning"]');
  await browser('find', 'first', 'a[href="/release-coordinator/release-planning"]', 'click');
  await browser('wait', '--url', `${appUrl}/release-coordinator/release-planning`);
  await browser('wait', 'a[href="/release-coordinator/release-planning/issues"]');
  await browser('click', 'a[href="/release-coordinator/release-planning/issues"]');
  await browser('wait', '--url', `${appUrl}/release-coordinator/release-planning/issues`);
  await browser('wait', '.issue-checkbox');
  await browser('find', 'role', 'checkbox', 'check', '--name', 'Check/Uncheck: Publish release', '--exact');
  await browser('find', 'role', 'checkbox', 'check', '--name', 'Check/Uncheck: Prepare release notes', '--exact');
  await browser('wait', '--fn', 'document.querySelectorAll(".issue-checkbox:checked").length === 2 && document.querySelector("#issue-actions").getBoundingClientRect().height > 0');
}
