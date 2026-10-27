#!/usr/bin/env bash
set -euo pipefail

cd /workspace/app/apps/api

export DATABASE_URL="${DATABASE_URL:-postgresql://plane:plane@plane-db:5432/plane}"
export REDIS_URL="${REDIS_URL:-redis://plane-redis:6379/}"
export SECRET_KEY="${SECRET_KEY:-dev-env-plane-local-development-only}"
export DJANGO_SETTINGS_MODULE="plane.settings.local"

/opt/plane-api/bin/python manage.py shell --settings=plane.settings.local <<'PY'
from uuid import UUID

from django.db import transaction
from django.db.models import Q

from plane.db.models import User, Workspace
from plane.license.models import Instance


USER_ID = UUID("11111111-1111-4111-8111-111111111111")
WORKSPACE_ID = UUID("22222222-2222-4222-8222-222222222222")
INSTANCE_MARKER = "editor-interactions-fixture"


with transaction.atomic():
    Workspace.all_objects.filter(Q(id=WORKSPACE_ID) | Q(slug="editor-interactions")).delete()
    User.objects.filter(Q(id=USER_ID) | Q(email="editor.review@example.com")).delete()

    instance = Instance.objects.select_for_update().first()
    if instance is not None and instance.namespace == INSTANCE_MARKER:
        instance.is_setup_done = False
        instance.namespace = None
        instance.save(update_fields=["is_setup_done", "namespace", "updated_at"])
PY
