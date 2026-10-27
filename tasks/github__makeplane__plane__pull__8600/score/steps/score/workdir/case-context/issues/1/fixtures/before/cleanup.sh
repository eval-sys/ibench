#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Runtime DATABASE_URL is required}"
: "${REDIS_URL:?Runtime REDIS_URL is required}"
cd /workspace/app/apps/api

/opt/plane-api/bin/python manage.py shell --settings=plane.settings.local <<'PY'
import uuid

from django.core.cache import cache
from django.db.models import Q

from plane.db.models import User, Workspace
from plane.license.models import Instance


USER_ID = uuid.UUID("86000000-0000-4000-8000-000000000001")
WORKSPACE_ID = uuid.UUID("86000000-0000-4000-8000-000000000002")
INSTANCE_ID = uuid.UUID("86000000-0000-4000-8000-000000000099")


Workspace.objects.filter(
    Q(id=WORKSPACE_ID) | Q(slug="content-operations")
).delete(soft=False)
User.objects.filter(
    Q(id=USER_ID) | Q(email="editor@example.com")
).delete()

instance = Instance.objects.first()
if instance is not None:
    if instance.id == INSTANCE_ID:
        instance.delete()
    else:
        instance.is_setup_done = False
        instance.save(update_fields=["is_setup_done"])
cache.delete("/api/instances/")
PY
