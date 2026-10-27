import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const run = (...args) => execFileAsync('agent-browser', args, {
  maxBuffer: 1024 * 1024,
  timeout: 120_000,
});

export default async function cleanup() {
  await run('network', 'unroute').catch(() => {});
  await run('cookies', 'clear').catch(() => {});
  await run('open', `${process.env.APP_URL || 'http://localhost:3000'}/#/auth/login`).catch(() => {});
  await run('storage', 'local', 'clear').catch(() => {});
  await run('storage', 'session', 'clear').catch(() => {});
}
