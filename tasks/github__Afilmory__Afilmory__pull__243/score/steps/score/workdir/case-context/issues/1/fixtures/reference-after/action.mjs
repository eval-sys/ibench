import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

const browser = (...args) =>
  execFileAsync('agent-browser', args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  })

export default async function action() {
  await browser('wait', '1200')

  await browser('swipe', 'left', '300')
  await browser('wait', '1000')
}
