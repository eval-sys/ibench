BEGIN;

DELETE FROM oauth_access_tokens
WHERE account_id = '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40';

DELETE FROM installed_apps
WHERE app_id = '5e2bb497-11fd-4d28-a68c-09c7c6623b31';

DELETE FROM sites
WHERE app_id = '5e2bb497-11fd-4d28-a68c-09c7c6623b31';

DELETE FROM workflows
WHERE app_id = '5e2bb497-11fd-4d28-a68c-09c7c6623b31';

DELETE FROM apps
WHERE id = '5e2bb497-11fd-4d28-a68c-09c7c6623b31';

DELETE FROM tenant_account_joins
WHERE id = 'f5d38307-948f-40e6-9c82-c4ae80bcc84e'
   OR account_id = '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40';

DELETE FROM accounts
WHERE id = '7f3a20d1-4fb4-48a2-ae5b-e754c6089a40';

COMMIT;
