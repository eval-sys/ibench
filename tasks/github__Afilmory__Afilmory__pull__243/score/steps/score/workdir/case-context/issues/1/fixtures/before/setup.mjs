import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

const browser = (...args) =>
  execFileAsync('agent-browser', args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  })

export default async function setup() {
  await browser('open', 'http://localhost:3210/')
  await browser('wait', '--text', 'landscape')
  await browser('find', 'role', 'gridcell', 'click', '--name', 'landscape')
  await browser('wait', '--url', '**/photos/landscape')
  await browser('wait', '[aria-label="View location in map"]')
  await browser('wait', '5000')
  await browser('scrollintoview', '[aria-label="View location in map"]')
  await browser('wait', '1500')
}
