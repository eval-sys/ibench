import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const base = (process.env.APP_URL || 'http://localhost:3000').replace(/\/$/, '');
const browser = async (...args) => {
  const { stdout } = await exec('agent-browser', args, { timeout: 30000 });
  if (stdout) process.stdout.write(stdout);
};

export default async function setup() {
  // The repository is public; this path needs no authentication.
  await browser('open', `${base}/`);
  await browser('find', 'role', 'link', 'click', '--name', 'Explore', '--exact');
  await browser('wait', '--url', `${base}/explore/repos`);
  await browser('find', 'placeholder', 'Search repos…', 'fill', 'project-notes');
  await browser('find', 'role', 'button', 'click', '--name', 'Search…', '--exact');
  await browser('wait', '--url', `${base}/explore/repos?only_show_relevant=false&q=project-notes&sort=recentupdate`);
  await browser('wait', 'a[href="/morgan-code/project-notes"]');
  await browser('click', 'a[href="/morgan-code/project-notes"]');
  await browser('wait', '--url', `${base}/morgan-code/project-notes`);
  await browser('wait', '.branch-dropdown-button');
}
