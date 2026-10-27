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

export default async function action() {
  await command('wait', '900')

  await command('find', 'role', 'button', 'click', '--name', 'Clean up accounts', '--exact')
  await command('wait', '--text', 'Account cleanup')
  await command('wait', '700')

  await command('find', 'label', 'Max photos', 'fill', '1', '--exact')
  await command('find', 'label', 'Max storage (MB)', 'fill', '1', '--exact')
  // Wait for both candidate rows, independently of the storage formatting.
  // This only reads rendered DOM; all form changes use user-facing commands.
  await command('wait', '--fn', `(() => {
    const rows = Array.from(document.querySelectorAll('[role="dialog"] tbody tr'))
    return rows.some(row => row.innerText.includes('small workspace') && row.innerText.includes('1 photo'))
      && rows.some(row => row.innerText.includes('empty workspace') && row.innerText.includes('0 photos'))
  })()`)
  const { stdout } = await command('snapshot')
  process.stdout.write(stdout)
}
