import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 30000 });

export default async function setup() {
  // The public signup form needs no account or seeded transactional records.
  await browser('open', 'http://localhost:3000/signup');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', 'input[name="name"]');
  await browser('find', 'label', 'Full Name', 'fill', 'Alex Morgan');
  await browser('find', 'label', 'Email Address', 'fill', 'alex');
  await browser('find', 'label', 'Password', 'fill', 'short');
  // Reveal before correction, so the visibility button cannot blur corrected input.
  await browser('find', 'role', 'button', 'click', '--name', 'Reveal password');
  await browser('find', 'label', 'Full Name', 'click');
  await browser('wait', '--text', 'Invalid email address');
  await browser('wait', '--text', 'Must be at least 8 characters in length');
  // Do not submit: validation after a submission has different revalidation rules.
}
