import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 30000 });

async function observe(phase, expectedFocus, expectedValue) {
  // DOM reads only: interactions below use the browser's click and keyboard commands.
  const result = await browser('eval', `(() => {
    const active = document.activeElement;
    if (active.name !== ${JSON.stringify(expectedFocus)} || active.value !== ${JSON.stringify(expectedValue)}) {
      throw new Error('The correction did not retain focus and the required value');
    }
    return { phase: ${JSON.stringify(phase)}, focus: active.name,
      fields: ['email', 'password'].map(name => {
        const element = document.querySelector('input[name="' + name + '"]');
        return { name, value: element.value, invalid: element.getAttribute('aria-invalid'),
          className: element.className, boxShadow: getComputedStyle(element).boxShadow,
          feedback: (element.getAttribute('aria-describedby') || '').split(' ')
            .map(id => document.getElementById(id)?.textContent || '').filter(Boolean) };
      }) };
  })()`);
  process.stdout.write(result.stdout);
}

export default async function action() {
  // Step 1: present the existing email and password validation errors.
  await browser('wait', '1500');
  process.stdout.write((await browser('screenshot')).stdout);

  // Step 2: append the missing email portion while keeping the email focused.
  await browser('find', 'label', 'Email Address', 'click');
  await browser('press', 'End');
  await browser('keyboard', 'type', '@example.com');
  await browser('wait', '500');
  await observe('Email correction, before blur', 'email', 'alex@example.com');
  process.stdout.write((await browser('screenshot')).stdout);
  await browser('wait', '1500');

  // Step 3: moving to Password blurs the corrected email.
  await browser('find', 'label', 'Password', 'click');
  await browser('wait', '1500');

  // Step 4: replace the password with valid input and keep it focused.
  await browser('press', 'Control+a');
  await browser('keyboard', 'type', 'Kestrel!482');
  await browser('wait', '500');
  await observe('Password correction, before blur', 'password', 'Kestrel!482');
  process.stdout.write((await browser('screenshot')).stdout);
  await browser('wait', '2000');
}
