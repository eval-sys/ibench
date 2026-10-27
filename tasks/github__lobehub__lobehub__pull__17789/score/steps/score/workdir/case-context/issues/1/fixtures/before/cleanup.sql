BEGIN;

DELETE FROM users
WHERE id = 'user_conversation_reader'
   OR email = 'conversation.reader@example.test'
   OR username = 'conversation-reader';

COMMIT;
