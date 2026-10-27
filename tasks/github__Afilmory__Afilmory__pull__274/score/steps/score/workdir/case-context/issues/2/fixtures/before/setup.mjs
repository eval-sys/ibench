import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

async function command(...args) {
  return execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  })
}

async function assertUrl(expected) {
  const { stdout } = await command('get', 'url')
  const actual = stdout.trim()
  if (actual !== expected) {
    throw new Error(`Expected browser URL ${expected}, received ${actual}`)
  }
}

export default async function setup() {
  await command('open', 'http://root.localhost:3210/platform/root-login')
  await command('wait', '--text', 'Root Administrator Login')
  await command('find', 'label', 'Email', 'fill', 'root@local.host', '--exact')
  await command('find', 'label', 'Password', 'fill', 'Local-Development-2026', '--exact')
  await command('find', 'role', 'button', 'click', '--name', 'Sign In', '--exact')
  await command('wait', '--url', '**/platform/superadmin/settings')
  await assertUrl('http://root.localhost:3210/platform/superadmin/settings')

  await command('find', 'role', 'link', 'click', '--name', 'Tenants', '--exact')
  await command('wait', '--url', '**/platform/superadmin/tenants')
  await assertUrl('http://root.localhost:3210/platform/superadmin/tenants')
  await command('wait', '--text', 'Tenant Subscription Management')
  await command('wait', '--text', 'small workspace')
  await command('wait', '--text', 'empty workspace')
}
