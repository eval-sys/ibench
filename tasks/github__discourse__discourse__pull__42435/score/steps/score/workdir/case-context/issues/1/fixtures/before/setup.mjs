import { execFileSync } from 'node:child_process';

export default async function setup() {
  const browser = (...args) => execFileSync('agent-browser', args, { encoding: 'utf8', timeout: 60000 });
  // The stream is public; authentication is unnecessary for this interaction.
  browser('open', 'http://localhost:3000/u/morgan_reader/activity/replies');
  browser('wait', '--fn', 'document.querySelectorAll(".user-stream-item").length === 30');
}
