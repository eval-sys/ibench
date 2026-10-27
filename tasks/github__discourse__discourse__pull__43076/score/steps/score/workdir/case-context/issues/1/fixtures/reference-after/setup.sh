#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"
cd /workspace/app
# Use the supported initial administrator entrypoint, rather than its internal steps.
printf '%s\n' 'morgan_review@example.com' 'ReviewPass!2026' 'ReviewPass!2026' 'y' | bundle exec rake admin:create
bundle exec rails runner - <<'RUBY'
staff = User.find_by_email("morgan_review@example.com")
staff.update!(username: "morgan_review", name: "Morgan", moderator: true)
author = User.create!(username: "casey_review", name: "Casey", email: "casey_review@example.com", password: "AuthorPass!2026", active: true, approved: true, trust_level: 0)
author.activate
Group.refresh_automatic_groups!(:staff, :admins, :moderators, :trust_level_0)
# Native services supply post counters, review scores, penalty history and system messages.
opener = PostCreator.create!(staff, title: "Community resource suggestions", raw: "Share useful resources for the community in this discussion.", skip_validations: true, skip_rate_limits: true)
post = PostCreator.create!(author, topic_id: opener.topic_id, raw: "Visit my promotion page for special offers and discount codes.", skip_validations: true, skip_rate_limits: true)
result = PostActionCreator.spam(staff, post)
raise "Flag did not create a pending review" unless result.reviewable&.pending?
post.reload
post.hide!(PostActionType.types[:spam]) unless post.hidden?
raise "Could not silence author" unless UserSilencer.silence(author.reload, Discourse.system_user, post_id: post.id, reason: "Silenced automatically") || author.reload.silenced?
raise "Missing post-linked silence" unless UserSilencer.was_silenced_for?(post)
puts "Review scenario ready for casey_review"
RUBY
