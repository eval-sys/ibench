#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
bundle exec rails runner - <<'RUBY'
# Stable email keys restrict cleanup to this issue's accounts and content.
users = %w[morgan_review@example.com casey_review@example.com].filter_map { |email| User.find_by_email(email) }
user_ids = users.map(&:id)
unless user_ids.empty?
  topic_ids = (Topic.with_deleted.where(user_id: user_ids).pluck(:id) + TopicAllowedUser.where(user_id: user_ids).pluck(:topic_id)).uniq
  post_ids = Post.with_deleted.where(topic_id: topic_ids).pluck(:id)
  Reviewable.where(target_created_by_id: user_ids).or(Reviewable.where(topic_id: topic_ids)).find_each(&:destroy!)
  topic_ids.each do |topic_id|
    first = Post.with_deleted.find_by(topic_id: topic_id, post_number: 1)
    PostDestroyer.new(Discourse.system_user, first, force_destroy: true, context: "Remove temporary review scenario").destroy if first
  end
  UserHistory.where(target_user_id: user_ids).or(UserHistory.where(acting_user_id: user_ids)).or(UserHistory.where(post_id: post_ids)).or(UserHistory.where(topic_id: topic_ids)).delete_all
  users.each(&:destroy!)
end
RUBY
