#!/usr/bin/env bash
set -euo pipefail

PGPASSWORD="${PENPOT_DATABASE_PASSWORD:-penpot}" \
  psql -h penpot-postgres -U "${PENPOT_DATABASE_USERNAME:-penpot}" -d penpot -v ON_ERROR_STOP=1 <<'SQL'
BEGIN;
SET LOCAL rules.deletion_protection = 'off';

CREATE TEMP TABLE fixture_profiles ON COMMIT DROP AS
SELECT id, default_team_id, default_project_id
FROM profile
WHERE email = 'layer-navigation-case@example.com';

CREATE TEMP TABLE fixture_seed_files ON COMMIT DROP AS
SELECT id, project_id
FROM file
WHERE id = '8a114270-0000-4000-8000-000000000001'::uuid;

CREATE TEMP TABLE fixture_teams ON COMMIT DROP AS
SELECT '8a114270-0000-4000-8000-000000000010'::uuid AS id
UNION
SELECT default_team_id FROM fixture_profiles WHERE default_team_id IS NOT NULL
UNION
SELECT p.team_id
FROM project p
JOIN fixture_seed_files f ON f.project_id = p.id;

CREATE TEMP TABLE fixture_projects ON COMMIT DROP AS
SELECT id FROM project WHERE team_id IN (SELECT id FROM fixture_teams)
UNION
SELECT default_project_id FROM fixture_profiles WHERE default_project_id IS NOT NULL
UNION
SELECT project_id FROM fixture_seed_files;

CREATE TEMP TABLE fixture_files ON COMMIT DROP AS
SELECT id FROM file WHERE project_id IN (SELECT id FROM fixture_projects)
UNION
SELECT '8a114270-0000-4000-8000-000000000001'::uuid;

UPDATE profile
SET default_team_id = NULL, default_project_id = NULL
WHERE id IN (SELECT id FROM fixture_profiles);

DELETE FROM task
WHERE props::text LIKE '%8a114270-0000-4000-8000-000000000001%'
   OR props::text LIKE '%layer-navigation-case@example.com%';
DELETE FROM audit_log WHERE profile_id IN (SELECT id FROM fixture_profiles);
DELETE FROM file_change WHERE file_id IN (SELECT id FROM fixture_files);
DELETE FROM file_data WHERE file_id IN (SELECT id FROM fixture_files);
DELETE FROM file_media_object WHERE file_id IN (SELECT id FROM fixture_files);
DELETE FROM file_object_thumbnail WHERE file_id IN (SELECT id FROM fixture_files);
DELETE FROM file_tagged_object_thumbnail WHERE file_id IN (SELECT id FROM fixture_files);
DELETE FROM file_thumbnail WHERE file_id IN (SELECT id FROM fixture_files);
DELETE FROM file WHERE id IN (SELECT id FROM fixture_files);
DELETE FROM team_font_variant WHERE team_id IN (SELECT id FROM fixture_teams);
DELETE FROM project WHERE id IN (SELECT id FROM fixture_projects);
DELETE FROM team WHERE id IN (SELECT id FROM fixture_teams);
DELETE FROM profile WHERE id IN (SELECT id FROM fixture_profiles);

COMMIT;
SQL
