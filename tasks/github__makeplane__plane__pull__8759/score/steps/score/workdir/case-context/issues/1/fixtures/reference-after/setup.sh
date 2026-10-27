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

from plane.db.models import (
    Issue,
    Profile,
    Project,
    ProjectIdentifier,
    ProjectMember,
    State,
    User,
    Workspace,
    WorkspaceMember,
)
from plane.license.models import Instance


USER_ID = UUID("11111111-1111-4111-8111-111111111111")
WORKSPACE_ID = UUID("22222222-2222-4222-8222-222222222222")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
ISSUE_ID = UUID("44444444-4444-4444-8444-444444444444")
STATE_IDS = [
    UUID("50000000-0000-4000-8000-000000000001"),
    UUID("50000000-0000-4000-8000-000000000002"),
    UUID("50000000-0000-4000-8000-000000000003"),
    UUID("50000000-0000-4000-8000-000000000004"),
    UUID("50000000-0000-4000-8000-000000000005"),
]
INSTANCE_MARKER = "editor-interactions-fixture"


with transaction.atomic():
    Workspace.all_objects.filter(Q(id=WORKSPACE_ID) | Q(slug="editor-interactions")).delete()
    User.objects.filter(Q(id=USER_ID) | Q(email="editor.review@example.com")).delete()

    instance = Instance.objects.select_for_update().first()
    if instance is None:
        raise RuntimeError("Plane instance record is missing")
    if not instance.is_setup_done:
        instance.is_setup_done = True
        instance.namespace = INSTANCE_MARKER
        instance.save(update_fields=["is_setup_done", "namespace", "updated_at"])

    user = User(
        id=USER_ID,
        username="editor-interactions-fixture",
        email="editor.review@example.com",
        display_name="Avery Morgan",
        first_name="Avery",
        last_name="Morgan",
        is_active=True,
        is_email_verified=True,
        is_password_autoset=False,
    )
    user.set_password("EditorHover2026!")
    user.save(force_insert=True)

    workspace = Workspace(
        id=WORKSPACE_ID,
        name="Editor Interactions",
        slug="editor-interactions",
        owner=user,
        timezone="UTC",
    )
    workspace.save(force_insert=True, created_by_id=USER_ID)

    Profile.objects.create(
        user=user,
        is_onboarded=True,
        is_tour_completed=True,
        is_navigation_tour_completed=True,
        last_workspace_id=WORKSPACE_ID,
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
    )

    workspace_member = WorkspaceMember(
        workspace=workspace,
        member=user,
        role=20,
        company_role="Product",
        is_active=True,
    )
    workspace_member.save(force_insert=True, created_by_id=USER_ID)

    project = Project(
        id=PROJECT_ID,
        workspace=workspace,
        name="Content Review",
        identifier="CONTENT",
        description="Editorial workflow",
        network=2,
        project_lead=user,
        timezone="UTC",
    )
    project.save(force_insert=True, created_by_id=USER_ID)
    ProjectIdentifier.objects.create(
        workspace=workspace,
        project=project,
        name=project.identifier,
        created_by=user,
    )

    project_member = ProjectMember(project=project, member=user, role=20, is_active=True)
    project_member.save(force_insert=True, created_by_id=USER_ID)

    state_specs = [
        ("Backlog", "#60646C", "backlog", True, 15000),
        ("Todo", "#60646C", "unstarted", False, 25000),
        ("In Progress", "#F59E0B", "started", False, 35000),
        ("Done", "#46A758", "completed", False, 45000),
        ("Cancelled", "#9AA4BC", "cancelled", False, 55000),
    ]
    states = []
    for state_id, (name, color, group, is_default, sequence) in zip(STATE_IDS, state_specs):
        state = State(
            id=state_id,
            project=project,
            workspace=workspace,
            name=name,
            color=color,
            group=group,
            default=is_default,
            sequence=sequence,
        )
        state.save(force_insert=True, created_by_id=USER_ID)
        states.append(state)

    project.default_state = states[0]
    project.save(update_fields=["default_state", "updated_at"], created_by_id=USER_ID)

    issue = Issue(
        id=ISSUE_ID,
        project=project,
        workspace=workspace,
        state=states[0],
        name="Review description blocks",
        description_html=(
            "<p>The rollout checklist is ready for review.</p>"
            "<p>Confirm each note can be reordered before publishing.</p>"
        ),
        priority="none",
    )
    issue.save(force_insert=True, created_by_id=USER_ID)
PY
