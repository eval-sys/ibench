import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

async function command(...args) {
  return execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
}

export default async function action() {
  // Hold the configured mappings, date format, amount option, and summary rows
  // on screen before performing the single reported interaction.
  await command('wait', '1800');
  await command('fill', '#csv-skip-end-lines', '2');
  await command(
    'wait',
    '--fn',
    `document.querySelector('#csv-skip-end-lines')?.value === '2' &&
      document.querySelector('#form_flip')?.checked === false &&
      Array.from(document.querySelectorAll('button')).some(button => button.textContent?.trim() === 'Choose field...')`,
  );
  await command('wait', '1500');
}
