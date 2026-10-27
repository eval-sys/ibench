import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });

export default async function action() {
  // Step 1: Present the already loaded catalog and its manufacturer column.
  await browser('wait', '3000');

  // Step 2: Follow the visible Devices navigation, then the bay's own link.
  await browser('find', 'role', 'link', 'click', '--name', 'Module Bay Types', '--exact');
  await browser('wait', '--text', 'SFP28 transceiver bay');
  await browser('find', 'role', 'link', 'click', '--name', 'SFP28 transceiver bay', '--exact');
  await browser('wait', '--text', 'Compatible Module Types');
  await browser('wait', '3000');

  // Step 3: Inspect the end of the list and the cards beneath it.
  await browser('scroll', 'down', '800');
  await browser('wait', '2500');

  // Step 4: Return to the bay heading and the first compatible entries.
  await browser('scroll', 'up', '800');
  await browser('wait', '3000');
}
