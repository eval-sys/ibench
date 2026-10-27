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

export default async function cleanup() {
  await command('open', 'http://root.localhost:3210/platform/root-login')
  await command('wait', '--load', 'domcontentloaded')
  await command('cookies', 'clear')
  await command('storage', 'local', 'clear')
  await command('storage', 'session', 'clear')
}
