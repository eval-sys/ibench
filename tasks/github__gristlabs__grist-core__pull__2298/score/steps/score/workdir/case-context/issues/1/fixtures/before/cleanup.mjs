import { execFileSync } from 'node:child_process';
const browser = (...args) => execFileSync('agent-browser', args, { encoding: 'utf8' }).trim();

export default async function cleanup() {
  browser('cookies', 'clear');
  // A fresh browser initially has about:blank, where web storage is unavailable.
  // After replay, clear guest preferences and any document navigation state.
  if (browser('get', 'url').startsWith('http://localhost:8484/')) {
    browser('storage', 'local', 'clear');
    browser('storage', 'session', 'clear');
  }
}
