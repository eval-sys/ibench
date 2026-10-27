import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const run = async (file, args) => {
  const { stderr, stdout } = await execFileAsync(file, args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  if (stdout) process.stdout.write(stdout);
  if (stderr) process.stderr.write(stderr);
  return stdout;
};

const browser = (...args) => run('agent-browser', args);

const completedMessagesSql = `
BEGIN;
INSERT INTO messages
  (id, role, content, model, provider, user_id, session_id, topic_id, parent_id, agent_id,
   created_at, updated_at, accessed_at)
VALUES
  ('msg_architecture_answer', 'assistant',
   'The review approved a staged rollout, audit logging, and a rollback window.',
   'gpt-4o-mini', 'openai', 'user_conversation_reader', 'session_conversation_archive',
   'topic_architecture_review', 'msg_architecture_seed', 'agent_conversation_archive',
   '2026-01-01 10:01:00+00', '2026-01-01 10:01:00+00', '2026-01-01 10:01:00+00'),
  ('msg_architecture_followup', 'user',
   'Please keep the rollback window at 30 minutes.',
   NULL, NULL, 'user_conversation_reader', 'session_conversation_archive',
   'topic_architecture_review', 'msg_architecture_answer', 'agent_conversation_archive',
   '2026-01-01 10:02:00+00', '2026-01-01 10:02:00+00', '2026-01-01 10:02:00+00'),
  ('msg_architecture_confirm', 'assistant',
   'Confirmed: the rollback window is 30 minutes.',
   'gpt-4o-mini', 'openai', 'user_conversation_reader', 'session_conversation_archive',
   'topic_architecture_review', 'msg_architecture_followup', 'agent_conversation_archive',
   '2026-01-01 10:03:00+00', '2026-01-01 10:03:00+00', '2026-01-01 10:03:00+00')
ON CONFLICT (id) DO NOTHING;
UPDATE topics
SET updated_at = '2026-01-01 10:04:00+00'
WHERE id = 'topic_architecture_review';
COMMIT;
`;

export default async function setup() {
  const appURL = process.env.APP_URL;
  if (!appURL) throw new Error('APP_URL is required');
  await browser('open', new URL('/signin', appURL).href);
  await browser('wait', '--load', 'domcontentloaded');
  await browser('wait', 'input[placeholder="Enter your email or username"]');
  await browser(
    'find',
    'placeholder',
    'Enter your email or username',
    'fill',
    'conversation.reader@example.test',
  );
  await browser(
    'find',
    'role',
    'checkbox',
    'check',
    '--name',
    'I have read and agree to the Terms and Conditions and Privacy Policy',
  );
  await browser('find', 'role', 'button', 'click', '--name', 'Next');
  await browser('wait', 'input[placeholder="Enter your password"]');
  await browser('find', 'placeholder', 'Enter your password', 'fill', 'Conversation!17789');
  await browser('find', 'role', 'button', 'click', '--name', 'Sign In');
  await browser('wait', '1000');

  await browser(
    'open',
    new URL('/agent/agent_conversation_archive/topic_architecture_review', appURL).href,
  );
  await browser('wait', '--text', 'Summarize the architecture review decisions.');
  await browser('wait', '1000');
  const initial = await browser('snapshot');
  if (!initial.includes('Summarize the architecture review decisions.') ||
      initial.includes('The review approved a staged rollout') ||
      initial.includes('Please keep the rollback window') ||
      initial.includes('Confirmed: the rollback window')) {
    throw new Error('Given not established: Architecture review must initially show only its seed');
  }

  // Age the initial snapshot naturally beyond the current 30-second verification
  // window. This prepares an earlier browser view, not a user-facing deadline.
  await browser('wait', '31000');

  await run('psql', [
    '-d',
    process.env.DATABASE_URL,
    '-v',
    'ON_ERROR_STOP=1',
    '-c',
    completedMessagesSql + `SELECT id, role, content FROM messages WHERE topic_id = 'topic_architecture_review' ORDER BY created_at;`,
  ]);
  await browser('wait', '500');
  const retained = await browser('snapshot');
  if (retained.includes('The review approved a staged rollout') ||
      retained.includes('Please keep the rollback window') ||
      retained.includes('Confirmed: the rollback window')) {
    throw new Error('Given not established: browser refreshed before the topic switch');
  }
}
