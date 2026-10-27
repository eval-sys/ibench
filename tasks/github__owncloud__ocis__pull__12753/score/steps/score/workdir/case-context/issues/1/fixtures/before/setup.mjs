import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function setup() {
  // Endpoint and prepared credentials come from /opt/dev-env-profile.sh.
  // setup.sh creates the document before this clean browser session starts.
  await browser('open', 'https://localhost:9200/');
  await browser('wait', 'input[name="username"]');
  await browser('find', 'label', 'Username', 'fill', 'admin');
  await browser('find', 'label', 'Password', 'fill', 'admin');
  await browser('find', 'role', 'button', 'click', '--name', 'Log in', '--exact');
  await browser('wait', '[data-test-resource-name="Meeting notes.txt"]');
  // Open through the file list so the app supplies the current file ID and context.
  await browser('find', 'role', 'link', 'click', '--name', 'Meeting notes.txt', '--exact');
  await browser('wait', '#app-top-bar-resource button');
  await browser('wait', '.cm-content');
  await browser('wait', '--fn', 'document.querySelector(".cm-content")?.textContent.includes("Discuss the project schedule and next steps.")');
  // Establish a nearby control as the starting keyboard position, without focusing the filename.
  await browser('focus', '#app-top-bar-close');
}
