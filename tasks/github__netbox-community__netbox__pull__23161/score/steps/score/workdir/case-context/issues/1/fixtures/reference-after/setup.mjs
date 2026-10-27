import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
async function browser(...args) {
  return exec('agent-browser', args, { timeout: 120000, maxBuffer: 1024 * 1024 });
}

export default async function setup() {
  const appURL = process.env.APP_URL || 'http://localhost:8080';
  // Nginx's application endpoint is documented in /opt/netbox-runtime/nginx.conf.
  // The imported upstream demo documents the admin/admin credentials.
  await browser('open', new URL('/login/', appURL).href);
  await browser('fill', '#id_username', 'admin');
  await browser('fill', '#id_password', 'admin');
  await browser('find', 'role', 'button', 'click', '--name', 'Sign In', '--exact');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', 'header [aria-label="Open user menu"]');
  await browser('open', new URL('/dcim/interfaces/?q=uplink0', appURL).href);
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--text', 'Akron Edge A');
  await browser('wait', '--text', 'Akron Edge B');
}
