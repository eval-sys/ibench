import { execFileSync } from 'node:child_process'

function command(...args) {
  return execFileSync('agent-browser', args, {
    encoding: 'utf8',
    env: process.env,
    maxBuffer: 1024 * 1024,
  }).trim()
}

function box(selector) {
  const output = command('get', 'box', selector)
  const values = Object.fromEntries(
    output
      .split('\n')
      .map(line => line.match(/^([a-z]+):\s+([\d.]+)$/))
      .filter(Boolean)
      .map(match => [match[1], Number(match[2])]),
  )

  if (![values.x, values.y, values.width, values.height].every(Number.isFinite))
    throw new Error(`Could not parse element box for ${selector}: ${output}`)

  return {
    x: Math.round(values.x + values.width / 2),
    y: Math.round(values.y + values.height / 2),
  }
}

function clickPoint({ x, y }) {
  command(
    'batch',
    '--bail',
    `mouse move ${x} ${y}`,
    'mouse down',
    'mouse up',
  )
}

export default async function action() {
  const features = box('button:has(.i-ri-apps-2-add-line)')
  const publish = box('button:has(.i-ri-arrow-down-s-line)')

  command('find', 'role', 'button', 'click', '--name', 'Publish', '--exact')
  command('find', 'text', 'Publish Update', 'click', '--exact')
  command('wait', '--text', 'Make sure all issues are resolved before publishing')
  command('hover', '[role="dialog"]')
  command('wait', '1000')

  const toastCenter = box('[role="dialog"]')
  command(
    'batch',
    '--bail',
    'click \'button[aria-label="Close notification"]\'',
    `mouse move ${toastCenter.x} ${toastCenter.y}`,
    'mouse down',
    'mouse up',
  )

  command('wait', '700')
  clickPoint(features)
  command('wait', '350')
  clickPoint(publish)
  command('wait', '350')
}
