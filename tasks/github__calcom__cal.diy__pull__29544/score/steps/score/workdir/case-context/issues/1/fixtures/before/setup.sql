BEGIN;

DELETE FROM users
WHERE email = 'morgan.security@example.com';

WITH fixture_user AS (
  INSERT INTO users (
    uuid,
    username,
    name,
    email,
    "emailVerified",
    "completedOnboarding",
    "timeZone",
    locale,
    "identityProvider",
    role
  )
  VALUES (
    '29544001-0000-4000-8000-000000000001'::uuid,
    'morgan-security',
    'Morgan Lee',
    'morgan.security@example.com',
    CURRENT_TIMESTAMP,
    true,
    'UTC',
    'en',
    'CAL',
    'USER'
  )
  RETURNING id
)
INSERT INTO "UserPassword" ("userId", hash)
SELECT id, '$2a$12$Imxr8QFnr2Zo2CX4V7kZzOrihq8frLoQ.tw04MngC2r1Hr2E0lBeK'
FROM fixture_user;

COMMIT;
