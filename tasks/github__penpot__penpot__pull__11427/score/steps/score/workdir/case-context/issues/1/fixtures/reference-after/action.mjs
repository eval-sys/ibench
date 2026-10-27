import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const command = (...arguments_) =>
  execFileAsync('agent-browser', arguments_, {
    env: process.env,
    timeout: 120_000,
  });

export default async function action() {
  await command('wait', '--text', '1 / 40');
  await command('wait', '1200');

  await command('find', 'role', 'button', 'click', '--name', 'Previous', '--exact');
  await command('wait', '--text', '40 / 40');
  await command('wait', '1200');
}
