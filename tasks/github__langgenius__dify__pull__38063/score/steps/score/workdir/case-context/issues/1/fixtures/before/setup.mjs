import { execFileSync } from 'node:child_process'

function command(...args) {
  return execFileSync('agent-browser', args, {
    encoding: 'utf8',
    env: process.env,
    maxBuffer: 1024 * 1024,
  }).trim()
}

export default async function setup() {
  command('open', 'http://localhost:3210/signin')
  command('wait', 'input[type="email"]')
  command('fill', 'input[type="email"]', 'studio.editor@local.host')
  command('fill', 'input[type="password"]', 'ReleaseFlow2026!')
  command('click', 'button[type="submit"]')
  command('wait', '--url', 'http://localhost:3210/')

  command('wait', 'a[href="/apps"]')
  command('click', 'a[href="/apps"]')
  command('wait', '--url', 'http://localhost:3210/apps')
  command('wait', 'input[aria-label="Search Applications"]')
  command('fill', 'input[aria-label="Search Applications"]', 'Support Release Flow')
  command('wait', '--text', 'Support Release Flow')
  command('find', 'role', 'link', 'click', '--name', 'Support Release Flow', '--exact')

  command('wait', '--url', 'http://localhost:3210/app/5e2bb497-11fd-4d28-a68c-09c7c6623b31/workflow')
  command('wait', 'button:has(.i-ri-apps-2-add-line)')
  command('wait', '500')
}
