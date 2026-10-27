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
  const rootUrl = new URL(process.env.APP_URL)
  if (!rootUrl.hostname.startsWith('root.')) rootUrl.hostname = `root.${rootUrl.hostname}`
  await command('open', new URL('/platform/root-login', rootUrl).href)
  await command('wait', '--load', 'domcontentloaded')
  await command('cookies', 'clear')
  await command('storage', 'local', 'clear')
  await command('storage', 'session', 'clear')
}
