BEGIN;

DELETE FROM report_dashboard
WHERE id = 7949001
   OR entity_id = 'lb79490dash0000000001';

DELETE FROM core_user
WHERE id = 7949001
   OR email = 'lobebench.pr79490@example.com'
   OR entity_id = 'lb79490user0000000001';

COMMIT;
