import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 30000 });

export default async function setup() {
  // The public signup form needs no account or seeded transactional records.
  await browser('open', new URL('/signup', process.env.APP_URL || 'http://localhost:3000').href);
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
  // Read-only verification of Given; no form state or events are injected.
  const given = await browser('eval', `(() => {
    const input = name => document.querySelector('input[name="' + name + '"]');
    const errors = element => (element.getAttribute('aria-describedby') || '').split(' ')
      .map(id => document.getElementById(id)?.textContent || '').join(' ');
    const email = input('email');
    const password = input('password');
    if (input('name').value !== 'Alex Morgan' || email.value !== 'alex' || password.value !== 'short'
      || password.type !== 'text' || document.activeElement === email || document.activeElement === password
      || email.getAttribute('aria-invalid') !== 'true' || password.getAttribute('aria-invalid') !== 'true'
      || !errors(email).includes('Invalid email address')
      || !errors(password).includes('Must be at least 8 characters in length')) {
      throw new Error('The required initial signup state was not established');
    }
    return { phase: 'Given', email: email.value, emailError: errors(email),
      password: password.value, passwordError: errors(password), focus: document.activeElement.name };
  })()`);
  process.stdout.write(given.stdout);
  // Do not submit: validation after a submission has different revalidation rules.
}
