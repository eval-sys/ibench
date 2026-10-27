import { execFile } from 'node:child_process';
import { writeFile } from 'node:fs/promises';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const csvPath = '/tmp/actual-pr-7827-import-settings.csv';
const csv = [
  'Posting;Description;Details;Value;Category',
  '31.08.2024;Corner Market;Groceries;-12.34;',
  '30.08.2024;Payroll;Monthly salary;2000.00;',
  '29.08.2024;Metro Transit;Train fare;-3.50;',
  'Statement summary;;;3 transactions;',
  'Closing balance;;;1984.16;',
].join('\n');

async function command(...args) {
  const { stdout } = await execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  return stdout;
}

async function clickButton(name) {
  await command('find', 'role', 'button', 'click', '--name', name, '--exact');
}

export default async function setup() {
  await writeFile(csvPath, csv, 'utf8');

  await command('open', 'http://localhost:3210/');
  await command('wait', '--text', "Where's the server?");
  await clickButton("Don't use a server");
  await command('wait', '--text', "Let's get started!");
  await clickButton('Start fresh');

  await command('wait', '--text', 'For Actual to be useful');
  await clickButton('Add account');
  await command('wait', '--text', 'Create a local account');
  await clickButton('Create a local account');
  await command('wait', '--text', 'Create Local Account');
  await command('fill', 'input[name="name"]', 'Statement Review');
  await clickButton('Create');

  await command('wait', '--text', 'Statement Review');
  await clickButton('Import');
  await command('upload', 'input[type="file"]', csvPath);
  await command('wait', '--text', 'CSV FIELDS');

  await command('click', '#csv-delimiter-select');
  await clickButton(';');
  await command(
    'wait',
    '--fn',
    `document.querySelector('#csv-delimiter-select')?.textContent?.includes(';') &&
      ['Description', 'Details', 'Posting'].every(label =>
        Array.from(document.querySelectorAll('button')).some(button => button.textContent?.trim() === label)
      )`,
  );

  // Configure Amount before Date so the current "Posting" label stays unique.
  await clickButton('Posting');
  await clickButton('Value');
  await clickButton('Choose field...');
  await clickButton('Posting');
  await clickButton('YYYY.MM.DD');
  await clickButton('DD.MM.YYYY');
  await command('check', '#form_flip');

  await command(
    'wait',
    '--fn',
    `document.querySelector('#form_flip')?.checked === true &&
      document.querySelector('#csv-skip-end-lines')?.value === '0' &&
      Array.from(document.querySelectorAll('button')).some(button => button.textContent?.trim() === 'DD.MM.YYYY')`,
  );
}
