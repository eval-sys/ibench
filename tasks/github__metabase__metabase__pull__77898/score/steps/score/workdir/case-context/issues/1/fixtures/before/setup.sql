BEGIN;

DELETE FROM core_user
WHERE email = 'invite-marketing-77898@example.test';

-- Remove a partial prior setup so this script is independently idempotent.
DELETE FROM report_dashboard
WHERE id = 7789801
   OR entity_id = 'UXW4533Dashboard00001';
DELETE FROM collection
WHERE id = 7789801
   OR entity_id = 'UXW4533Collection0001';
DELETE FROM permissions_group
WHERE id IN (7789801, 7789802)
   OR entity_id IN ('UXW4533Marketing00001', 'UXW4533SalesGroup0001');
DELETE FROM user_key_value
WHERE user_id = 7789801;
DELETE FROM core_user
WHERE id = 7789801
   OR email = 'repro-admin-77898@example.test'
   OR entity_id = 'UXW4533AdminUser00001';

INSERT INTO core_user (
  id,
  email,
  first_name,
  last_name,
  password,
  password_salt,
  date_joined,
  is_superuser,
  is_active,
  is_qbnewb,
  is_datasetnewb,
  type,
  entity_id,
  is_data_analyst
) VALUES (
  7789801,
  'repro-admin-77898@example.test',
  'Repro',
  'Admin',
  '$2a$10$eOcFuvYocG/fW8ixZlKO/eGF4QfPXHCF9Z2IZ9BC9jr6GZ.MEOoKW',
  '86e65af3-b8be-449c-b4e7-6108a3304684',
  now(),
  TRUE,
  TRUE,
  FALSE,
  FALSE,
  'personal',
  'UXW4533AdminUser00001',
  FALSE
);

INSERT INTO auth_identity (
  id,
  user_id,
  provider,
  credentials,
  created_at,
  updated_at,
  confirmed_at
) VALUES (
  7789801,
  7789801,
  'password',
  '{"password_hash":"$2a$10$eOcFuvYocG/fW8ixZlKO/eGF4QfPXHCF9Z2IZ9BC9jr6GZ.MEOoKW","password_salt":"86e65af3-b8be-449c-b4e7-6108a3304684"}',
  now(),
  now(),
  now()
);

INSERT INTO permissions_group_membership (
  id,
  user_id,
  group_id,
  is_group_manager
)
SELECT 7789801, 7789801, id, FALSE
FROM permissions_group
WHERE magic_group_type = 'all-internal-users';

INSERT INTO permissions_group_membership (
  id,
  user_id,
  group_id,
  is_group_manager
)
SELECT 7789802, 7789801, id, FALSE
FROM permissions_group
WHERE magic_group_type = 'admin';

INSERT INTO permissions_group (
  id,
  name,
  entity_id,
  magic_group_type,
  is_tenant_group
) VALUES
  (7789801, 'Marketing', 'UXW4533Marketing00001', NULL, FALSE),
  (7789802, 'Sales', 'UXW4533SalesGroup0001', NULL, FALSE);

INSERT INTO collection (
  id,
  name,
  description,
  archived,
  location,
  slug,
  entity_id,
  created_at,
  is_sample,
  archived_directly,
  is_remote_synced
) VALUES (
  7789801,
  'Invite Access Demo',
  'Dashboard shared with Sales, not Marketing',
  FALSE,
  '/',
  'invite_access_demo',
  'UXW4533Collection0001',
  now(),
  FALSE,
  FALSE,
  FALSE
);

INSERT INTO report_dashboard (
  id,
  created_at,
  updated_at,
  name,
  description,
  creator_id,
  parameters,
  show_in_getting_started,
  enable_embedding,
  archived,
  collection_id,
  entity_id,
  auto_apply_filters,
  width,
  view_count,
  archived_directly,
  last_viewed_at
) VALUES (
  7789801,
  now(),
  now(),
  'Campaign Performance',
  'Dashboard used to verify invite group choices',
  7789801,
  '[]',
  FALSE,
  FALSE,
  FALSE,
  7789801,
  'UXW4533Dashboard00001',
  TRUE,
  'fixed',
  0,
  FALSE,
  now()
);

INSERT INTO permissions (
  id,
  object,
  group_id,
  perm_value,
  perm_type,
  collection_id
) VALUES (
  7789801,
  '/collection/7789801/read/',
  7789802,
  'read',
  'perms/collection-access',
  7789801
);

COMMIT;
