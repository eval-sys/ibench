#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
# Native Firebase emulator and Oppia HTTP registration/admin endpoints.
/opt/oppia-python/bin/python - <<'PYTHON'
import os, sys
sys.path[:0] = ['/workspace/app', '/workspace/app/third_party/python_libs']
os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:8089'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'dev-project-id'
import requests, hashlib, json
from core.platform import models
store = models.Registry.import_datastore_services()
cache = models.Registry.import_cache_services()
(config_models,) = models.Registry.import_models([models.Names.CONFIG])
class LanguageSelectionFixtureOwnership(store.Model):
    created_flag = store.BooleanProperty(default=False)
FLAG = 'enable_automatic_translation_suggestions'
# Preserve whether the configuration already existed; only the fixture group
# is appended to an existing configuration. No generated identifiers are saved.
with store.get_ndb_context(global_cache=store.RedisCache(cache.get_cloud_ndb_redis_client())):
    if LanguageSelectionFixtureOwnership.get_by_id('27464-1') is None:
        LanguageSelectionFixtureOwnership(id='27464-1', created_flag=(
            config_models.FeatureFlagConfigModel.get(FLAG, strict=False) is None
        )).put()
EMAIL = 'language.manager@example.com'
USERNAME = 'LanguageManager'
FIREBASE = 'http://localhost:9099/identitytoolkit.googleapis.com/v1/'
APP = os.environ['APP_URL'].rstrip('/')
password = hashlib.md5(EMAIL.encode()).hexdigest()
def auth_call(path, data, admin=False):
    r = requests.post(FIREBASE + path, json=data, headers={'Authorization':'Bearer owner'} if admin else {}, timeout=30)
    r.raise_for_status()
    return r.json()
r=requests.post(FIREBASE+'accounts:signInWithPassword?key=fake-api-key',json={'email':EMAIL,'password':password,'returnSecureToken':True},timeout=30)
if r.status_code != 200:
    assert r.json()['error']['message'] == 'EMAIL_NOT_FOUND', r.text
    account=auth_call('accounts:signUp?key=fake-api-key', {'email':EMAIL,'password':password,'returnSecureToken':True})
else:
    account=r.json()
auth_call('projects/dev-project-id/accounts:update', {'localId':account['localId'],'customAttributes':json.dumps({'role':'super_admin'})}, True)
account=auth_call('accounts:signInWithPassword?key=fake-api-key',{'email':EMAIL,'password':password,'returnSecureToken':True})
s=requests.Session()
s.get(APP+'/session_begin',headers={'Authorization':'Bearer '+account['idToken']},timeout=30).raise_for_status()
def app_call(method,path,payload=None):
    if payload is None:
        r=s.request(method,APP+path,timeout=30)
    else:
        csrf=s.get(APP+'/csrfhandler',timeout=30)
        csrf.raise_for_status()
        token=json.loads(csrf.text[5:])['token']
        r=s.request(method,APP+path,data={'csrf_token':token,'payload':json.dumps(payload)},timeout=30)
    if r.status_code >= 400: raise RuntimeError((r.status_code,r.text))
    return json.loads(r.text[5:])
s.get(APP+'/signup?return_url=/contributor-admin-dashboard',timeout=30).raise_for_status()
registration=app_call('GET','/signuphandler/data')
if not registration['has_ever_registered']:
    app_call('POST','/signuphandler/data',{'username':USERNAME,'agreed_to_terms':True,'default_dashboard':'contributor','can_receive_email_updates':False})
else:
    assert registration['username']==USERNAME
roles=app_call('GET','/adminrolehandler?filter_criterion=username&username='+USERNAME)['roles']
for role in ['TRANSLATION_ADMIN','RELEASE_COORDINATOR']:
    if role not in roles:
        app_call('PUT','/adminrolehandler',{'username':USERNAME,'role':role})
groups=app_call('GET','/user_groups_handler')['user_group_dicts']
group=next((g for g in groups if g['name']=='Translation configuration administrators'),None)
if group is None:
    group=app_call('POST','/user_groups_handler',{'name':'Translation configuration administrators','member_usernames':[USERNAME]})['user_group_dict']
flags=app_call('GET','/feature_flags')['feature_flags']
flag=next(f for f in flags if f['name']=='enable_automatic_translation_suggestions')
config=flag
app_call('PUT','/feature_flags',{'action':'update_feature_flag','feature_flag_name':flag['name'],'force_enable_for_all_users':config['force_enable_for_all_users'],'rollout_percentage':config['rollout_percentage'],'user_group_ids':list(dict.fromkeys(config['user_group_ids']+[group['user_group_id']]))})
configuration=app_call('GET','/translation-provider-mapping')
assert configuration['provider_mapping'] == {}, 'This scenario requires the unmodified, empty provider mapping.'
assert configuration['automatic_translation_is_enabled'] is False, 'The separate automatic-suggestions switch must be off.'
print('LanguageManager and its feature group are ready.')

PYTHON
