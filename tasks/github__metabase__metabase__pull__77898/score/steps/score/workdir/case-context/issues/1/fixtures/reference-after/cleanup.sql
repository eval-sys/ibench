BEGIN;

DELETE FROM core_user
WHERE email = 'invite-marketing-77898@example.test';

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

COMMIT;
