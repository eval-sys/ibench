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

from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from plane.db.models import FileAsset, Profile, User, Workspace, WorkspaceMember, WorkspaceUserProperties
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

Instance.objects.create(
    instance_name="Creative Studio",
    instance_id=INSTANCE_ID,
    current_version="1.3.1",
    domain="localhost",
    last_checked_at=timezone.now(),
    is_setup_done=True,
    is_signup_screen_visited=True,
    is_verified=True,
    is_test=True,
)

user = User.objects.create(
    email=EMAIL,
    username=USERNAME,
    password=make_password("Canvas-Profile-2026!"),
    first_name="Avery",
    last_name="Morgan",
    display_name="Avery.Morgan",
    is_active=True,
    is_email_verified=True,
    cover_image="http://localhost:3000/assets/image_1-8ncaj2f5.jpg",
)
profile = Profile.objects.create(
    user=user,
    role="Product Designer",
    is_onboarded=True,
    is_tour_completed=True,
    is_navigation_tour_completed=True,
    onboarding_step={
        "profile_complete": True,
        "workspace_create": True,
        "workspace_invite": False,
        "workspace_join": True,
    },
    product_tour={
        "work_items": True,
        "cycles": True,
        "modules": True,
        "intake": True,
        "pages": True,
    },
)
workspace = Workspace.objects.create(name="Creative Studio", slug=WORKSPACE_SLUG, owner=user)
WorkspaceMember.objects.create(workspace=workspace, member=user, role=20)
WorkspaceUserProperties.objects.create(workspace=workspace, user=user)
profile.last_workspace_id = workspace.id
profile.save(update_fields=["last_workspace_id"])
cache.clear()
PY
