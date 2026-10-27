import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
async function browser(...args) {
  await exec('agent-browser', args, { timeout: 120000 });
}

export default async function action() {
  // Step 1: present the existing Given, established by setup.
  await browser('wait', '1800');

  // Step 2: add one customer through the visible Tom Select picker.
  await browser('fill', '#customers-ts-control', 'Westbridge');
  await browser('wait', '.ts-dropdown [data-selectable]');
  await browser('wait', '600'); // Make the matching option inspectable.
  await browser('find', 'role', 'option', 'click', '--name', 'Westbridge Services', '--exact');
  await browser('wait', '--load', 'networkidle');
  // Remove the option popup so both customer and project selections are visible.
  await browser('focus', '#search-dropdown-btn');
  await browser('wait', '1800');
}
