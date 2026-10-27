#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"

# Reuse the account and device definitions from the immutable demo imported by
# /opt/dev-env-profile.sh (netbox-demo-data commit faeae5904a29ce6ad519a3de270ca218a7b050f9).
# That dump has no ObjectChange records. Isolated devices supply the missing
# cable history without disconnecting or deleting any prepared demo objects.
cd /workspace/app
venv/bin/python netbox/manage.py shell <<'PY'
import uuid
from django.db import transaction
from django.test import RequestFactory
from dcim.models import Cable, Device, DeviceRole, DeviceType, Interface, Site
from netbox.context_managers import event_tracking
from users.models import User

user = User.objects.get(username='admin', is_superuser=True, is_active=True)
site = Site.objects.get(slug='dm-akron')
role = DeviceRole.objects.get(slug='router')
device_type = DeviceType.objects.get(slug='mx80')

def request():
    req = RequestFactory().get('/')
    req.id = uuid.uuid4()
    req.user = user
    return req

with transaction.atomic():
    with event_tracking(request()):
        devices = [Device.objects.create(
            name=name, site=site, role=role, device_type=device_type,
            description='Dedicated cable history review.'
        ) for name in ('Akron Edge A', 'Akron Edge B')]
        interfaces = [Interface.objects.create(
            device=device, name='uplink0', type='1000base-t'
        ) for device in devices]

    # These are the application's real cable operations and request event
    # tracking. Do not insert or manufacture ObjectChange rows.
    with event_tracking(request()):
        cable = Cable(
            a_terminations=[interfaces[0]], b_terminations=[interfaces[1]],
            label='Akron interconnect', type='cat6', status='connected',
            description='Dedicated cable history review.'
        )
        cable.save()
    with event_tracking(request()):
        cable.delete()

    for interface in interfaces:
        interface.refresh_from_db()
        assert interface.cable_id is None
PY
