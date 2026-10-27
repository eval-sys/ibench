BEGIN;

DELETE FROM users
WHERE id = 'user_conversation_reader'
   OR email = 'conversation.reader@example.test'
   OR username = 'conversation-reader';

INSERT INTO users
  (id, username, email, full_name, is_onboarded, preference, email_verified,
   normalized_email, onboarding, created_at, updated_at, accessed_at, last_active_at)
VALUES
  ('user_conversation_reader', 'conversation-reader', 'conversation.reader@example.test',
   'Conversation Reader', TRUE, '{"locale":"en-US"}'::jsonb, TRUE,
   'conversation.reader@example.test',
   '{"version":2,"currentStep":4,"finishedAt":"2026-01-01T09:00:00.000Z"}'::jsonb,
   '2026-01-01 09:00:00+00', '2026-01-01 09:00:00+00',
   '2026-01-01 09:00:00+00', '2026-01-01 09:00:00+00');

INSERT INTO accounts
  (id, account_id, provider_id, password, user_id, created_at, updated_at)
VALUES
  ('account_conversation_reader', 'user_conversation_reader', 'credential',
   '$2b$10$DCeG4vA9je5aE6ETQQVoj.a9wrfXaMkmcwTyQT1dPsceoj2X0eDES',
   'user_conversation_reader', '2026-01-01 09:00:00', '2026-01-01 09:00:00');

INSERT INTO agents
  (id, slug, title, description, tags, user_id, model, params, provider, system_role,
   created_at, updated_at, accessed_at, visibility)
VALUES
  ('agent_conversation_archive', 'conversation-archive', 'Project Assistant',
   'Keeps project discussion notes organized.', '[]'::jsonb, 'user_conversation_reader',
   'gpt-4o-mini', '{}'::jsonb, 'openai', 'Help organize project decisions.',
   '2026-01-01 09:01:00+00', '2026-01-01 09:01:00+00',
   '2026-01-01 09:01:00+00', 'public');

INSERT INTO sessions
  (id, slug, title, description, type, user_id, created_at, updated_at, accessed_at)
VALUES
  ('session_conversation_archive', 'conversation-archive', 'Project Assistant',
   'Project discussion archive', 'agent', 'user_conversation_reader',
   '2026-01-01 09:01:00+00', '2026-01-01 09:01:00+00',
   '2026-01-01 09:01:00+00');

INSERT INTO agents_to_sessions (agent_id, session_id, user_id)
VALUES
  ('agent_conversation_archive', 'session_conversation_archive',
   'user_conversation_reader');

INSERT INTO topics
  (id, session_id, user_id, title, agent_id, status, created_at, updated_at, accessed_at)
VALUES
  ('topic_architecture_review', 'session_conversation_archive',
   'user_conversation_reader', 'Architecture review', 'agent_conversation_archive', 'active',
   '2026-01-01 10:00:00+00', '2026-01-01 10:00:00+00',
   '2026-01-01 10:00:00+00'),
  ('topic_daily_agenda', 'session_conversation_archive',
   'user_conversation_reader', 'Today''s agenda', 'agent_conversation_archive', 'active',
   '2026-01-02 10:00:00+00', '2026-01-02 10:02:00+00',
   '2026-01-02 10:02:00+00');

INSERT INTO messages
  (id, role, content, model, provider, user_id, session_id, topic_id, parent_id, agent_id,
   created_at, updated_at, accessed_at)
VALUES
  ('msg_architecture_seed', 'user', 'Summarize the architecture review decisions.',
   NULL, NULL, 'user_conversation_reader', 'session_conversation_archive',
   'topic_architecture_review', NULL, 'agent_conversation_archive',
   '2026-01-01 10:00:00+00', '2026-01-01 10:00:00+00', '2026-01-01 10:00:00+00'),
  ('msg_agenda_seed', 'user', 'What is on today''s agenda?',
   NULL, NULL, 'user_conversation_reader', 'session_conversation_archive',
   'topic_daily_agenda', NULL, 'agent_conversation_archive',
   '2026-01-02 10:00:00+00', '2026-01-02 10:00:00+00', '2026-01-02 10:00:00+00'),
  ('msg_agenda_answer', 'assistant',
   'Review the handoff notes, then open the architecture review.',
   'gpt-4o-mini', 'openai', 'user_conversation_reader', 'session_conversation_archive',
   'topic_daily_agenda', 'msg_agenda_seed', 'agent_conversation_archive',
   '2026-01-02 10:01:00+00', '2026-01-02 10:01:00+00', '2026-01-02 10:01:00+00');

COMMIT;
