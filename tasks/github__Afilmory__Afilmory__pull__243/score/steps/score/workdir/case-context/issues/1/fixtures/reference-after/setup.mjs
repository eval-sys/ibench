import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

const browser = (...args) =>
  execFileAsync('agent-browser', args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  })

export default async function setup() {
  await browser('open', new URL('/', process.env.APP_URL).href)
  await browser('wait', '--text', 'landscape')
  await browser('find', 'role', 'gridcell', 'click', '--name', 'landscape')
  await browser('wait', '--url', '**/photos/landscape')
  await browser('wait', '[aria-label="View location in map"]')
  await browser('scrollintoview', '[aria-label="View location in map"]')
  await browser('wait', '--fn', `!Array.from(document.querySelectorAll('a')).find(e => e.getAttribute('aria-label') === 'View location in map').parentElement.innerText.includes('Loading map')`)

  // Follow the sidebar link into its actual new tab. Recording starts in that
  // tab with Given established, immediately before the map-pan action.
  await browser('find', 'role', 'link', 'click', '--name', 'View location in map', '--exact')
  await browser('wait', '--url', '**/explory?photoId=landscape')
  await browser('wait', '[aria-label="Map marker"]')
  await browser('find', 'role', 'link', 'text', '--name', 'landscape', '--exact')
  await browser('wait', '--load', 'networkidle')
  await browser('wait', '1500')
}
