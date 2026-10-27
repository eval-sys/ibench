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

async function refFor(role, name) {
  const { stdout } = await command('snapshot', '-i', '--json')
  const refs = JSON.parse(stdout).data?.refs ?? {}
  const entry = Object.entries(refs).find(([, value]) => value.role === role && value.name === name)
  if (!entry) {
    throw new Error(`Could not find ${role} named ${name}`)
  }
  return `@${entry[0]}`
}

export default async function action() {
  await command('wait', '900')

  await command('focus', await refFor('button', 'Clean up accounts'))
  await command('press', 'Enter')
  await command('wait', '--text', 'Account cleanup')
  await command('wait', '700')

  await command('find', 'label', 'Max photos', 'fill', '1', '--exact')
  await command('find', 'label', 'Max storage (MB)', 'fill', '1', '--exact')
  await command('wait', '--text', '0 photos')
  await command('wait', '--text', '1 photo')
  await command('wait', '--text', '0.0 MB')
}
