#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"
cd /workspace/app
# Supported first-administrator setup, scoped to the account owned by this issue.
printf '%s\n' 'morgan_reader@example.invalid' 'RiverWalking2026!' 'RiverWalking2026!' 'y' | bin/rake admin:create
bin/rails runner - <<'RUBY'
user = User.find_by_email('morgan_reader@example.invalid')
raise 'Account setup failed' unless user&.admin?
user.update!(username: 'morgan_reader', name: 'Morgan Reed', approved: true, active: true)
UserActionManager.enable
# Fixed content and dates: the general demo populate task generates random records.
5.times do |group|
  first = PostCreator.new(user,
    title: "Weekend walking plans #{format('%02d', group + 1)}",
    raw: "Let's collect route notes for this weekend walk. Share landmarks, rest stops, and useful paths.",
    created_at: Time.utc(2026, 9, 1) + group * 8 * 60,
    skip_validations: true, skip_jobs: true, skip_events: true
  ).create!
  8.times do |index|
    note = group * 8 + index + 1
    PostCreator.new(user,
      topic_id: first.topic_id,
      raw: "Route note #{format('%02d', note)}: The riverside path has a quiet rest stop beside the old bridge. This is a useful place to pause, check the map, and plan the next stretch of the walk.",
      created_at: Time.utc(2026, 9, 1) + note * 60,
      skip_validations: true, skip_jobs: true, skip_events: true
    ).create!
  end
end
raise 'Missing replies' unless UserAction.where(user_id: user.id, action_type: UserAction::REPLY).count == 40
RUBY
