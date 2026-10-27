BEGIN;

DELETE FROM report_dashboard
WHERE id = 7949001
   OR entity_id = 'lb79490dash0000000001';

DELETE FROM core_user
WHERE id = 7949001
   OR email = 'lobebench.pr79490@example.com'
   OR entity_id = 'lb79490user0000000001';

INSERT INTO core_user (
  id,
  email,
  first_name,
  last_name,
  password,
  password_salt,
  date_joined,
  updated_at,
  is_superuser,
  is_active,
  is_qbnewb,
  is_datasetnewb,
  locale,
  type,
  entity_id,
  is_data_analyst
) VALUES (
  7949001,
  'lobebench.pr79490@example.com',
  'Lobebench',
  'Reviewer',
  '$2a$10$d8N.GaVyS9BHAilrFLelD.wHjC.FajTIJnT.oITwMsHACqqoRYlzC',
  '79490000-0000-4000-8000-000000000001',
  now(),
  now(),
  true,
  true,
  false,
  false,
  'en',
  'personal',
  'lb79490user0000000001',
  false
);

INSERT INTO auth_identity (
  id,
  user_id,
  provider,
  provider_id,
  credentials,
  metadata,
  created_at,
  updated_at,
  confirmed_at
) VALUES (
  7949001,
  7949001,
  'password',
  'lobebench.pr79490@example.com',
  json_build_object(
    'password_hash', '$2a$10$d8N.GaVyS9BHAilrFLelD.wHjC.FajTIJnT.oITwMsHACqqoRYlzC',
    'password_salt', '79490000-0000-4000-8000-000000000001'
  )::text,
  NULL,
  now(),
  now(),
  now()
);

INSERT INTO permissions_group_membership (id, user_id, group_id)
SELECT 79490010, 7949001, id
FROM permissions_group
WHERE name = 'All Users';

INSERT INTO permissions_group_membership (id, user_id, group_id)
SELECT 79490011, 7949001, id
FROM permissions_group
WHERE name = 'Administrators';

INSERT INTO report_dashboard (
  id,
  created_at,
  updated_at,
  name,
  description,
  creator_id,
  parameters,
  archived,
  enable_embedding,
  entity_id,
  width
) VALUES (
  7949001,
  now(),
  now(),
  'PR 79490 Empty Dashboard',
  'Empty dashboard used to reproduce PDF export feedback.',
  7949001,
  '[]',
  false,
  false,
  'lb79490dash0000000001',
  'fixed'
);

COMMIT;
