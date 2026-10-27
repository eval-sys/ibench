import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const hold = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export default async function action() {
  const browser = (...args) => exec('agent-browser', args, { encoding: 'utf8', timeout: 60000 });

  // Step 1: Scroll through the first page, load the remaining replies, and
  // present the reading position at Route note 05 (the 36th reply).
  // Read-only screenshots ensure the recorder receives each stable view.
  await browser('screenshot', '/tmp/activity-stream-initial.png');
  await hold(1000);
  await browser('scroll', 'down', '10000');
  await browser('wait', '--fn', 'document.querySelectorAll(".user-stream-item").length === 40');
  await browser('scrollintoview', '.user-stream-item:nth-child(36)');
  await browser('screenshot', '/tmp/activity-stream-reading.png');
  await hold(1800);

  // Step 2: Follow the visible title link for that reply.
  await browser('click', '.user-stream-item:nth-child(36) .title a');
  await browser('wait', '#topic-title');
  await browser('screenshot', '/tmp/activity-stream-topic.png');
  await hold(1800);

  // Step 3: Browser Back reveals the restored stream and its reading position.
  await browser('back');
  await browser('wait', '.user-stream-item');
  await hold(2500);
}
