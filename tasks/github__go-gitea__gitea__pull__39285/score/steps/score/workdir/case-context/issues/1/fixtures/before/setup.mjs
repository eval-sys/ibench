import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => {
  const { stdout } = await exec('agent-browser', args, { timeout: 30000 });
  if (stdout) process.stdout.write(stdout);
};

export default async function setup() {
  // The repository is public; this path needs no authentication.
  await browser('open', 'http://localhost:3000/');
  await browser('find', 'role', 'link', 'click', '--name', 'Explore', '--exact');
  await browser('wait', '--url', 'http://localhost:3000/explore/repos');
  await browser('find', 'placeholder', 'Search repos…', 'fill', 'project-notes');
  await browser('find', 'role', 'button', 'click', '--name', 'Search…', '--exact');
  await browser('wait', '--url', 'http://localhost:3000/explore/repos?only_show_relevant=false&q=project-notes&sort=recentupdate');
  await browser('wait', 'a[href="/morgan-code/project-notes"]');
  await browser('click', 'a[href="/morgan-code/project-notes"]');
  await browser('wait', '--url', 'http://localhost:3000/morgan-code/project-notes');
  await browser('wait', '.branch-dropdown-button');
}
