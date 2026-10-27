import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 35000 });

// Read-only diagnostics. All navigation, submission, entry and blur use the CLI's
// user-facing commands; this does not dispatch events or alter application state.
async function observe(stage) {
  const { stdout } = await browser('eval', `(() => {
    const e = document.querySelector('#new_user_name');
    const s = getComputedStyle(e);
    return { stage: ${JSON.stringify(stage)}, url: location.href,
      value: e.value, focused: document.activeElement === e,
      required: e.required, pattern: e.pattern, valid: e.validity.valid,
      userInvalid: e.matches(':user-invalid'), message: e.validationMessage,
      border: s.border, shadow: s.boxShadow,
      users: [...document.querySelectorAll('#user-list .username')].map(e => e.textContent),
      notification: document.querySelector('#notification')?.textContent.trim() };
  })()`);
  console.log(stdout.trim());
}

export default async function action() {
  // Step 1: Present the existing Display page and current theme.
  await browser('wait', '1500');

  // Step 2: Follow the visible admin navigation to the password confirmation.
  await browser('scrollintoview', '#aside_feed a[href$="?c=user&a=manage"]');
  await browser('find', 'role', 'link', 'click', '--name', 'Manage users', '--exact');
  await browser('wait', '--text', 'Reauthentication is required');
  await browser('wait', '1200');

  // Step 3: Complete the prompt; leave every Create new user field untouched.
  await browser('fill', '#passwordPlain', 'profile-development');
  await browser('wait', 'button[type="submit"]:not([disabled])');
  await browser('wait', '800');
  await browser('find', 'role', 'button', 'click', '--name', 'Login', '--exact');
  await browser('wait', '#new_user_name');
  await browser('wait', '2500');
  await observe('first opening, untouched');

  // Additional Require checks follow only after the original When has ended.
  await browser('find', 'role', 'button', 'click', '--name', 'Create', '--exact');
  await browser('wait', '1800');
  await observe('empty submission');

  await browser('fill', '#new_user_name', 'bad name!');
  await browser('find', 'role', 'button', 'click', '--name', 'Create', '--exact');
  await browser('wait', '1800');
  await observe('malformed submission');

  await browser('fill', '#new_user_name', 'verifier9025');
  await browser('press', 'Tab');
  await browser('wait', '1800');
  await observe('corrected username, unfocused');

  await browser('fill', '#new_user_passwordPlain', 'verify-password-9025');
  await browser('find', 'role', 'button', 'click', '--name', 'Create', '--exact');
  await browser('wait', '--text', 'User verifier9025 has been created');
  await browser('wait', '--fn', "[...document.querySelectorAll('#user-list .username')].some(e => e.textContent === 'verifier9025')");
  await observe('successful creation');
  await browser('scrollintoview', '#user-list tbody tr:last-child');
  await browser('wait', '2000');
}
