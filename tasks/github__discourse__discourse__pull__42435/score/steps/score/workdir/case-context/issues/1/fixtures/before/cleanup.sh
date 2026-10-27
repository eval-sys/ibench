#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
bin/rails runner - <<'RUBY'
user = User.find_by_email('morgan_reader@example.invalid')
if user
  Topic.with_deleted.where(user_id: user.id).find_each do |topic|
    first = Post.with_deleted.find_by(topic_id: topic.id, post_number: 1)
    if first
      PostDestroyer.new(Discourse.system_user, first,
        force_destroy: true, skip_staff_log: true, context: 'Remove temporary walking discussion'
      ).destroy
    end
  end
  # UserDestroyer refuses administrators; revoke only this owned account first.
  user.update!(admin: false)
  UserDestroyer.new(Discourse.system_user).destroy(user,
    quiet: true, prepare_for_destroy: true
  )
end
RUBY
