#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
/opt/oppia-python/bin/python - <<'PYTHON'
import os, sys
sys.path[:0] = ['/workspace/app', '/workspace/app/third_party/python_libs']
os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:8089'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'dev-project-id'
import requests
from core import feconf
from core.platform import models
from core.domain import fs_services
store = models.Registry.import_datastore_services()
cache = models.Registry.import_cache_services()
(user_models, config_models, base_models, audit_models) = models.Registry.import_models([
    models.Names.USER, models.Names.CONFIG, models.Names.BASE_MODEL, models.Names.AUDIT])
class LanguageSelectionFixtureOwnership(store.Model):
    created_flag = store.BooleanProperty(default=False)
EMAIL = 'language.manager@example.com'
USERNAME = 'LanguageManager'
FLAG = 'enable_automatic_translation_suggestions'
with store.get_ndb_context(global_cache=store.RedisCache(cache.get_cloud_ndb_redis_client())):
    ownership = LanguageSelectionFixtureOwnership.get_by_id('27464-1')
    users = user_models.UserSettingsModel.query(user_models.UserSettingsModel.email == EMAIL).fetch()
    for user in users:
        assert user.username in (None, USERNAME), 'Refusing to remove a different account.'
    user_ids = {user.id for user in users}
    groups = user_models.UserGroupModel.query(
        user_models.UserGroupModel.name == 'Translation configuration administrators').fetch()
    for group in groups:
        assert set(group.user_ids).issubset(user_ids), 'Refusing to remove a shared group.'
    group_ids = {group.id for group in groups}
    flag = config_models.FeatureFlagConfigModel.get(FLAG, strict=False)
    if flag is not None and group_ids.intersection(flag.user_group_ids):
        flag.user_group_ids = [group_id for group_id in flag.user_group_ids if group_id not in group_ids]
        flag.update_timestamps()
        flag.put()
    if (ownership is not None and ownership.created_flag and flag is not None
            and not flag.user_group_ids and not flag.force_enable_for_all_users
            and flag.rollout_percentage == 0):
        flag.delete()
    for group in groups:
        group.delete()
    # Native per-user deletion policies clear signup, auth, preferences and
    # activity records. Audit records created by this account also belong to it.
    for user in users:
        fs = fs_services.GcsFileSystem(feconf.ENTITY_TYPE_USER, USERNAME)
        for filename in ['profile_picture.png', 'profile_picture.webp']:
            if fs.isfile(filename):
                fs.delete(filename)
        for model_class in models.Registry.get_storage_model_classes([models.Names.AUTH, models.Names.USER]):
            if model_class.get_deletion_policy() in (
                base_models.DELETION_POLICY.DELETE, base_models.DELETION_POLICY.DELETE_AT_END):
                model_class.apply_deletion_policy(user.id)
        for audit in audit_models.RoleQueryAuditModel.query(audit_models.RoleQueryAuditModel.user_id == user.id).fetch():
            audit.delete()
    if ownership is not None:
        ownership.key.delete()
# Resolve the emulator account by its fixed email, even after a partial signup.
endpoint = 'http://localhost:9099/identitytoolkit.googleapis.com/v1/projects/dev-project-id/'
headers = {'Authorization': 'Bearer owner'}
r = requests.post(endpoint+'accounts:lookup', json={'email':[EMAIL]}, headers=headers, timeout=30)
r.raise_for_status()
for account in r.json().get('users', []):
    assert account['email'] == EMAIL
    r = requests.post(endpoint+'accounts:delete', json={'localId':account['localId']}, headers=headers, timeout=30)
    r.raise_for_status()
print('Language selection fixture state cleared.')
PYTHON
