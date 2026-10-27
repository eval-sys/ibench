#!/usr/bin/env bash
set -euo pipefail

# Runtime database and storage settings are inherited from the profile environment.
cd /workspace/app/apps/api

/opt/plane-api/bin/python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.local")

import django
import boto3

django.setup()

from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db.models import Q
from plane.db.models import FileAsset, User, Workspace
from plane.license.models import Instance

EMAIL = "avery.morgan@example.com"
USERNAME = "avery-morgan-profile"
WORKSPACE_SLUG = "creative-studio"
INSTANCE_ID = "creative-studio-local"

users = list(User.objects.filter(Q(email=EMAIL) | Q(username=USERNAME)))
user_ids = {str(user.id) for user in users}

for session in Session.objects.iterator():
    try:
        session_user_id = str(session.get_decoded().get("_auth_user_id", ""))
    except Exception:
        continue
    if session_user_id in user_ids:
        session.delete()

s3 = boto3.client("s3", endpoint_url="http://plane-rustfs:9000")
for asset_key in FileAsset.all_objects.filter(user__in=users).values_list("asset", flat=True):
    if asset_key:
        s3.delete_object(Bucket="uploads", Key=asset_key)

Workspace.all_objects.filter(Q(slug=WORKSPACE_SLUG) | Q(owner__in=users)).delete()
User.objects.filter(id__in=[user.id for user in users]).delete()
Instance.all_objects.filter(instance_id=INSTANCE_ID).delete()
cache.clear()
PY
