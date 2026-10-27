#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
venv/bin/python netbox/manage.py shell <<'PY'
from django.db import transaction
from dcim.models import ModuleBayType, ModuleType

catalog = 'Optical transceiver compatibility catalog'
with transaction.atomic():
    generic_models = ['SFP-25G-SR-C'] + [f'SFP-25G-ZR-{i:02d}' for i in range(1, 36)]
    ModuleType.objects.filter(description=catalog, manufacturer__slug='generic',
                              model__in=generic_models).delete()
    ModuleType.objects.filter(description=catalog, manufacturer__slug='cisco',
                              model__in=['SFP-25G-SR-C', 'SFP-25G-ZR']).delete()
    ModuleBayType.objects.filter(slug='sfp28-transceiver-bay',
                                description=catalog, manufacturer__isnull=True).delete()
PY
