import { execFileSync } from 'node:child_process'

function command(...args) {
  return execFileSync('agent-browser', args, {
    encoding: 'utf8',
    env: process.env,
    maxBuffer: 1024 * 1024,
  }).trim()
}

export default async function cleanup() {
  command('open', 'http://localhost:3210/')

  try {
    command('eval', `
      (async () => {
        const csrfCookie = document.cookie
          .split('; ')
          .find(cookie => cookie.startsWith('csrf_token='))
        const csrfToken = csrfCookie ? decodeURIComponent(csrfCookie.split('=').slice(1).join('=')) : ''
        await fetch('http://localhost:5001/console/api/logout', {
          method: 'POST',
          credentials: 'include',
          headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {},
        })
      })()
    `)
  }
  catch {
    // An unauthenticated browser has no server session to revoke.
  }

  command('storage', 'local', 'clear')
  command('storage', 'session', 'clear')
  command('cookies', 'clear')
}
