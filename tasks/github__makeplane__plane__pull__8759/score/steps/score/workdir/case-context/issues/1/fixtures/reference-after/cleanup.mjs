import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const command = async (...args) => {
  await execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
};

export default async function cleanup() {
  await command('open', `${process.env.APP_URL || 'http://localhost:3000'}/`);
  await command('cookies', 'clear');
  await command('storage', 'local', 'clear');
  await command('storage', 'session', 'clear');
}
