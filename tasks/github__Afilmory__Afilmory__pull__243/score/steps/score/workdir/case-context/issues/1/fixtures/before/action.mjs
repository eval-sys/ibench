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

  const { stdout } = await browser('tab', 'list', '--json')
  const recordingTab = JSON.parse(stdout).data.tabs.find(tab => tab.active)?.tabId
  if (!recordingTab) {
    throw new Error('Unable to identify the active recording tab')
  }

  await browser('find', 'role', 'link', 'click', '--name', 'View location in map', '--exact')
  await browser('wait', '--url', '**/explory?photoId=landscape')
  await browser('wait', '[aria-label="Map marker"]')
  await browser('find', 'role', 'link', 'text', '--name', 'landscape', '--exact')

  // target="_blank" leaves the installed recorder on the source tab. Mirror the
  // verified click destination there so the captured transition remains inspectable.
  await browser('tab', recordingTab)
  await browser('open', 'http://localhost:3210/explory?photoId=landscape')
  await browser('wait', '[aria-label="Map marker"]')
  await browser('find', 'role', 'link', 'text', '--name', 'landscape', '--exact')
  await browser('wait', '1500')

  await browser('swipe', 'left', '300')
  await browser('wait', '1000')
}
