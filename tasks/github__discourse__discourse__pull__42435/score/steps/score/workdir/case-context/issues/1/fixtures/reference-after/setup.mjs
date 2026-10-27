import { execFileSync } from 'node:child_process';

export default async function setup() {
  const browser = (...args) => execFileSync('agent-browser', args, { encoding: 'utf8', timeout: 60000 });
  // The stream is public; authentication is unnecessary for this interaction.
  browser('open', new URL('/u/morgan_reader/activity/replies', process.env.APP_URL).href);
  browser('wait', '--fn', 'document.querySelectorAll(".user-stream-item").length === 30');
}
