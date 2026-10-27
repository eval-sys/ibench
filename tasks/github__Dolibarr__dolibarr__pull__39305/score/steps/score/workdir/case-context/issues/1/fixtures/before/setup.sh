#!/usr/bin/env bash
set -euo pipefail
# The environment imports dev/initdemo/mysqldump_dolibarr_22.0.0.sql.
# Reuse its admin and Teclib; isolate the proposal because the action changes prices.
bash "$(dirname "${BASH_SOURCE[0]}")/cleanup.sh"
php <<'PHP'
<?php
require '/workspace/app/htdocs/master.inc.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/admin.lib.php';
require_once DOL_DOCUMENT_ROOT.'/comm/propal/class/propal.class.php';
if ($user->fetch('', 'admin') <= 0) throw new Exception('Missing prepared admin');
$user->loadRights();
if (!isModEnabled('margin')) throw new Exception('Prepared Margin module is required');
$r=$db->query("SELECT rowid FROM ".MAIN_DB_PREFIX."societe WHERE code_client='CU1108-0001' AND nom='Teclib'");
$s=$db->fetch_object($r);
if (!$s) throw new Exception('Missing prepared Teclib');
$r=$db->query("SELECT value FROM ".MAIN_DB_PREFIX."const WHERE name='DISPLAY_MARK_RATES' AND entity=1");
$c=$db->fetch_object($r);
if ($c && $c->value != '1') throw new Exception('Unexpected existing mark-rate configuration');
if (!$c && dolibarr_set_const($db,'DISPLAY_MARK_RATES','1','chaine',0,'Owned by PR39305 interaction fixture',1)<=0) throw new Exception($db->lasterror());
$p=new Propal($db);
$p->socid=$s->rowid;
$p->date=dol_mktime(12,0,0,10,4,2026);
$p->duree_validite=30;
$p->ref_client='Service pricing';
$p->ref_ext='interaction-39305-1';
$p->model_pdf='azur';
if ($p->create($user,1)<=0) throw new Exception($p->error);
foreach ([['Consulting service',100,80],['Planning service',50,40]] as [$desc,$price,$cost]) {
    if ($p->addline($desc,$price,1,0,0,0,0,0,'HT',0,0,1,-1,0,0,0,$cost)<=0) throw new Exception($p->error);
}
PHP
