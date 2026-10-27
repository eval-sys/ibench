import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const appURL = (process.env.APP_URL || 'http://localhost:3000').replace(/\/$/, '');

const command = (...arguments_) =>
  execFileAsync('agent-browser', arguments_, {
    env: process.env,
    timeout: 120_000,
  });

export default async function cleanup() {
  await command('open', appURL);
  await command('storage', 'local', 'clear');
  await command('storage', 'session', 'clear');
  await command('cookies', 'clear');
}
