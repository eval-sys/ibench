#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
venv/bin/python netbox/manage.py shell <<'PY'
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Q
from core.models import ObjectChange
from dcim.models import Cable, Device, Interface

names = ('Akron Edge A', 'Akron Edge B')
label = 'Akron interconnect'
with transaction.atomic():
    devices = Device.objects.filter(name__in=names)
    device_ids = list(devices.values_list('pk', flat=True))
    interface_ids = list(Interface.objects.filter(device_id__in=device_ids).values_list('pk', flat=True))
    device_type = ContentType.objects.get_for_model(Device)
    interface_type = ContentType.objects.get_for_model(Interface)
    owned_changes = ObjectChange.objects.filter(
        Q(object_repr__in=(*names, label))
        | Q(object_repr__startswith=f'Cable {label} to ')
        | Q(changed_object_type=device_type, changed_object_id__in=device_ids)
        | Q(related_object_type=device_type, related_object_id__in=device_ids)
        | Q(changed_object_type=interface_type, changed_object_id__in=interface_ids)
        | Q(related_object_type=interface_type, related_object_id__in=interface_ids)
    )
    # Every matching request belongs exclusively to this scenario. Grouping
    # by request also clears native component and termination history after a
    # partially completed setup, even when the cable has already been deleted.
    request_ids = list(owned_changes.values_list('request_id', flat=True).distinct())
    Cable.objects.filter(label=label).delete()
    devices.delete()
    ObjectChange.objects.filter(request_id__in=request_ids).delete()
PY
