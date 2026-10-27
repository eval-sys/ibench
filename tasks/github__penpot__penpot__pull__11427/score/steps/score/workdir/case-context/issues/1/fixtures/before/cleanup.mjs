import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const command = (...arguments_) =>
  execFileAsync('agent-browser', arguments_, {
    env: process.env,
    timeout: 120_000,
  });

export default async function cleanup() {
  await command('open', 'http://localhost:3000');
  await command('storage', 'local', 'clear');
  await command('storage', 'session', 'clear');
  await command('cookies', 'clear');
}
