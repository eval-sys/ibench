#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Runtime DATABASE_URL is required}"
: "${REDIS_URL:?Runtime REDIS_URL is required}"
cd /workspace/app/apps/api

/opt/plane-api/bin/python manage.py shell --settings=plane.settings.local <<'PY'
import uuid

from django.core.cache import cache
from django.utils import timezone

from plane.db.models import (
    Issue,
    Profile,
    Project,
    ProjectMember,
    State,
    User,
    Workspace,
    WorkspaceMember,
)
from plane.license.models import Instance


USER_ID = uuid.UUID("86000000-0000-4000-8000-000000000001")
WORKSPACE_ID = uuid.UUID("86000000-0000-4000-8000-000000000002")
PROJECT_ID = uuid.UUID("86000000-0000-4000-8000-000000000003")
STATE_ID = uuid.UUID("86000000-0000-4000-8000-000000000004")
PROFILE_ID = uuid.UUID("86000000-0000-4000-8000-000000000005")
ISSUE_ONE_ID = uuid.UUID("86000000-0000-4000-8000-000000000010")
ISSUE_TWO_ID = uuid.UUID("86000000-0000-4000-8000-000000000011")
INSTANCE_ID = uuid.UUID("86000000-0000-4000-8000-000000000099")


Workspace.objects.filter(slug="content-operations").delete(soft=False)
Workspace.objects.filter(id=WORKSPACE_ID).delete(soft=False)
User.objects.filter(email="editor@example.com").delete()
User.objects.filter(id=USER_ID).delete()

instance = Instance.objects.first()
if instance is None:
    instance = Instance.objects.create(
        id=INSTANCE_ID,
        instance_name="Plane",
        instance_id="86000000-0000-4000-8000-000000000099",
        domain="localhost:3000",
        current_version="1.2.0",
        latest_version="1.2.0",
        last_checked_at=timezone.now(),
        is_setup_done=True,
    )
else:
    instance.is_setup_done = True
    instance.save(update_fields=["is_setup_done"])
cache.delete("/api/instances/")

user = User(
    id=USER_ID,
    username="editor@example.com",
    email="editor@example.com",
    display_name="Content Editor",
    first_name="Content",
    last_name="Editor",
    is_active=True,
    is_email_verified=True,
    is_email_valid=True,
)
user.set_password("PlaneIssue8600!")
user.save()

Profile.objects.create(
    id=PROFILE_ID,
    user=user,
    is_onboarded=True,
    is_tour_completed=True,
    is_navigation_tour_completed=True,
    onboarding_step={
        "profile_complete": True,
        "workspace_create": True,
        "workspace_invite": True,
        "workspace_join": True,
    },
    product_tour={
        "work_items": True,
        "cycles": True,
        "modules": True,
        "intake": True,
        "pages": True,
    },
    last_workspace_id=WORKSPACE_ID,
    background_color="#2563EB",
)

workspace = Workspace.objects.create(
    id=WORKSPACE_ID,
    name="Content Operations",
    slug="content-operations",
    owner=user,
    organization_size="1-10",
    background_color="#2563EB",
    created_by=user,
    updated_by=user,
)
WorkspaceMember.objects.create(
    workspace=workspace,
    member=user,
    role=20,
    created_by=user,
    updated_by=user,
)

project = Project.objects.create(
    id=PROJECT_ID,
    workspace=workspace,
    name="Editorial Calendar",
    identifier="EDIT",
    description="Editorial planning and review",
    project_lead=user,
    created_by=user,
    updated_by=user,
)
ProjectMember.objects.create(
    project=project,
    workspace=workspace,
    member=user,
    role=20,
    created_by=user,
    updated_by=user,
)

state = State.objects.create(
    id=STATE_ID,
    workspace=workspace,
    project=project,
    name="Planned",
    description="Ready for editorial work",
    color="#3B82F6",
    group="backlog",
    sequence=1000,
    default=True,
    created_by=user,
    updated_by=user,
)

Issue.objects.create(
    id=ISSUE_ONE_ID,
    workspace=workspace,
    project=project,
    state=state,
    name="[EDIT-1:title] Prepare launch brief",
    description_html="<p>[EDIT-1:desc] Outline goals for the launch and list the primary audience.</p>",
    priority="medium",
    created_by=user,
    updated_by=user,
)
Issue.objects.create(
    id=ISSUE_TWO_ID,
    workspace=workspace,
    project=project,
    state=state,
    name="[EDIT-2:title] Review research notes",
    description_html="<p>[EDIT-2:desc] Summarize customer interviews and capture the key findings.</p>",
    priority="medium",
    created_by=user,
    updated_by=user,
)
PY
