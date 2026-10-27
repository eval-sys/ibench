#!/usr/bin/env bash
set -euo pipefail
# The profile imports the pinned upstream v4.6 demo and runs native upgrades.
# Reuse its admin account and manufacturer slugs; compatibility records are missing.
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"
cd /workspace/app
venv/bin/python netbox/manage.py shell <<'PY'
from django.db import transaction
from dcim.models import Manufacturer, ModuleBayType, ModuleType

catalog = 'Optical transceiver compatibility catalog'
with transaction.atomic():
    cisco = Manufacturer.objects.get(slug='cisco', name='Cisco')
    generic = Manufacturer.objects.get(slug='generic', name='Generic')
    bay = ModuleBayType(name='SFP28 transceiver bay', slug='sfp28-transceiver-bay',
                        color='2196f3', description=catalog)
    bay.full_clean()
    bay.save()
    # Insert in a different order from display order to distinguish it from ID order.
    entries = [(generic, f'SFP-25G-ZR-{i:02d}') for i in range(35, 0, -1)]
    entries += [(generic, 'SFP-25G-SR-C'), (cisco, 'SFP-25G-ZR'), (cisco, 'SFP-25G-SR-C')]
    for manufacturer, model in entries:
        module = ModuleType(manufacturer=manufacturer, model=model, description=catalog)
        module.full_clean()
        module.save()
        module.module_bay_types.add(bay)
    assert bay.module_types.count() == 38
PY
