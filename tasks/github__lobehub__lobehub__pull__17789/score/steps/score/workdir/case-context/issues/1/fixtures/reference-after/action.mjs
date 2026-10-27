import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';

const execFileAsync = promisify(execFile);

const browser = async (...args) => {
  const { stderr, stdout } = await execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  if (stdout) process.stdout.write(stdout);
  if (stderr) process.stderr.write(stderr);
  return stdout;
};

export default async function action() {
  await browser('wait', '1200');
  const initial = await browser('snapshot');
  if (!initial.includes('Summarize the architecture review decisions.') ||
      initial.includes('The review approved a staged rollout') ||
      initial.includes('Please keep the rollback window') ||
      initial.includes('Confirmed: the rollback window')) {
    throw new Error('Given not established: recording must start with the earlier one-message view');
  }

  await browser('find', 'role', 'link', 'click', '--name', "Today's agenda");
  await browser(
    'wait',
    '--url',
    '**/agent/agent_conversation_archive/topic_daily_agenda',
  );
  await browser('wait', '--text', 'Review the handoff notes, then open the architecture review.');
  await browser('wait', '1200');
  await browser('snapshot');
  await browser('network', 'requests', '--clear');
  await browser('network', 'har', 'start');

  await browser('find', 'role', 'link', 'click', '--name', 'Architecture review');
  await browser(
    'wait',
    '--url',
    '**/agent/agent_conversation_archive/topic_architecture_review',
  );
  await browser('wait', '--text', 'Summarize the architecture review decisions.');
  await browser('wait', '5000');
  await browser('snapshot');
  await browser('eval', `JSON.stringify({
    phase: 'returned-conversation',
    messages: [
      'Summarize the architecture review decisions.',
      'The review approved a staged rollout, audit logging, and a rollback window.',
      'Please keep the rollback window at 30 minutes.',
      'Confirmed: the rollback window is 30 minutes.',
    ].map(content => ({
      content,
      visible: document.body.innerText.includes(content),
      position: document.body.innerText.indexOf(content),
    })),
  })`);
  await browser('network', 'requests', '--filter', 'message.getMessages');
  await browser(
    'network',
    'har',
    'stop',
    fileURLToPath(new URL('../evidence/message-requests.har', import.meta.url)),
  );
}
