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

export default async function action() {
  command('find', 'role', 'button', 'click', '--name', 'Publish', '--exact')
  command('find', 'text', 'Publish Update', 'click', '--exact')
  command('wait', '--text', 'Make sure all issues are resolved before publishing')
  command('hover', '[role="dialog"]')
  command('wait', '1000')

  const toastCenter = box('[role="dialog"]')
  const dismissalStarted = Date.now()
  command(
    'batch',
    '--bail',
    'click \'button[aria-label="Close notification"]\'',
    `mouse move ${toastCenter.x} ${toastCenter.y}`,
    'mouse down',
    'mouse up',
  )

  console.log('Dismissal and immediate center click elapsed ms:', Date.now() - dismissalStarted)
  console.log('Exiting toast (read-only):', command('eval', `JSON.stringify([...document.querySelectorAll('[role="dialog"]')].map(element => ({ ending: element.hasAttribute('data-ending-style'), opacity: getComputedStyle(element).opacity, pointerEvents: getComputedStyle(element).pointerEvents, afterPointerEvents: getComputedStyle(element, '::after').pointerEvents })))`))
  command('wait', '700')
  console.log('After dismissal:', command('get', 'count', '[role="dialog"]'))
  command('find', 'role', 'button', 'click', '--name', 'Features', '--exact')
  command('wait', '--text', 'Conversation Opener')
  console.log('After Features:', command('snapshot', '-i'))
  command('wait', '700')
  command('find', 'role', 'button', 'click', '--name', 'Close', '--exact')
  command('wait', '350')
  command('find', 'role', 'button', 'click', '--name', 'Publish', '--exact')
  command('wait', '--text', 'Publish Update')
  console.log('After Publish:', command('snapshot', '-i'))
  command('wait', '700')
}
