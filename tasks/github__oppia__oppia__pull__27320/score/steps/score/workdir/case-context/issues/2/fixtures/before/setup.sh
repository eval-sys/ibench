#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
# Use the installed Oppia runtime and its native datastore/domain services.
export PYTHONPATH=/workspace/app:/workspace/app/third_party/python_libs
export GOOGLE_CLOUD_PROJECT=dev-project-id
export DATASTORE_EMULATOR_HOST=127.0.0.1:8089
export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
exec /opt/oppia-python/bin/python - setup 2 <<'PYTHON'
import hashlib, json, sys
from pathlib import Path
from core.platform import models
from core.domain import feature_flag_services, exp_fetchers, exp_services, user_services, wipeout_service, wipeout_domain, fs_services
from core.platform.auth import firebase_auth_services
from firebase_admin import auth

mode, issue = sys.argv[1:]
state_file = Path('/tmp/oppia-report-' + issue + '-preconditions.json')
flags = ['web_feedback_modal_enabled'] + (['new_lesson_player'] if issue == '2' else [])
email = 'lesson.reader@example.com'
store = models.Registry.import_datastore_services()
config_models, user_models = models.Registry.import_models([models.Names.CONFIG, models.Names.USER])
with store.get_ndb_context():
 firebase_auth_services.establish_firebase_connection('dev-project-id')
 if mode == 'setup':
  if not state_file.exists():
   previous = feature_flag_services.load_feature_flags_from_storage(flags)
   state = {'flags': {name: (None if flag is None else {'force_enable_for_all_users': flag.feature_flag_config.force_enable_for_all_users, 'rollout_percentage': flag.feature_flag_config.rollout_percentage, 'user_group_ids': flag.feature_flag_config.user_group_ids}) for name, flag in previous.items()}, 'demo_owned': issue == '2' and exp_fetchers.get_exploration_by_id('0', strict=False) is None}
   state_file.write_text(json.dumps(state, default=str))
  state = json.loads(state_file.read_text())
  for name in flags:
   feature_flag_services.update_feature_flag(name, True, 0, [])
  if issue == '2':
   if exp_fetchers.get_exploration_by_id('0', strict=False) is None:
    exp_services.load_demo('0')
   try:
    account = auth.get_user_by_email(email)
   except auth.UserNotFoundError:
    account = auth.create_user(email=email, password=hashlib.md5(email.encode()).hexdigest(), email_verified=True)
   user = user_services.get_user_settings_by_auth_id(account.uid, strict=False)
   if user is None:
    user = user_services.create_new_user(account.uid, email)
   if not user.username:
    user_services.set_username(user.user_id, 'LessonReader')
   user_services.record_agreement_to_terms(user.user_id)
   user_services.update_email_preferences(user.user_id, False, False, False, False, can_receive_contributor_dashboard_email=False)
 else:
  if issue == '2':
   # Resolve every trial by its fixed email, including interrupted deletions.
   for model in user_models.UserSettingsModel.query(user_models.UserSettingsModel.email == email).fetch():
    request = wipeout_domain.PendingDeletionRequest.create_default(model.id, model.username or 'LessonReader', email)
    wipeout_service.delete_user(request)
    request.deletion_complete = True
    result = wipeout_service.run_user_deletion_completion(request)
    assert result == wipeout_domain.USER_VERIFICATION_SUCCESS, result
    user_models.DeletedUserModel.delete_by_id(model.id)
   try:
    account = auth.get_user_by_email(email)
    auth.delete_user(account.uid)
   except auth.UserNotFoundError:
    pass
  if state_file.exists():
   state = json.loads(state_file.read_text())
   if state['demo_owned']:
    exp_services.delete_demo('0')
    # Native demo deletion retains analytics and assets. These belong to this
    # issue only when it loaded the missing demo, as recorded before setup.
    exp_models, stats_models = models.Registry.import_models([models.Names.EXPLORATION, models.Names.STATISTICS])
    for cls, field in [
        (exp_models.ExplorationCommitLogEntryModel, 'exploration_id'),
        (exp_models.ExplorationVersionHistoryModel, 'exploration_id'),
        (stats_models.ExplorationIssuesModel, 'exp_id'),
        (stats_models.ExplorationStatsModel, 'exp_id'),
        (stats_models.StartExplorationEventLogEntryModel, 'exploration_id'),
        (stats_models.StateHitEventLogEntryModel, 'exploration_id'),
        (stats_models.MaybeLeaveExplorationEventLogEntryModel, 'exploration_id'),
    ]:
     for model in cls.query(getattr(cls, field) == '0').fetch():
      cls.delete_by_id(model.id)
    for model in stats_models.StateCounterModel.query().fetch():
     if model.id.startswith('0.'):
      stats_models.StateCounterModel.delete_by_id(model.id)
    fs = fs_services.GcsFileSystem('exploration', '0')
    for asset in fs.listdir(''):
     fs.delete(asset)
   for name, config in state['flags'].items():
    if config is None:
     model = config_models.FeatureFlagConfigModel.get(name, strict=False)
     if model:
      model.delete()
    else:
     feature_flag_services.update_feature_flag(name, config['force_enable_for_all_users'], config['rollout_percentage'], config['user_group_ids'])
   state_file.unlink()
PYTHON
