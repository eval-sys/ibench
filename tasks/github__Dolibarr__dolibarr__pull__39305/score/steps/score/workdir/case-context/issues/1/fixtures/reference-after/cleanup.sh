#!/usr/bin/env bash
set -euo pipefail
php <<'PHP'
<?php
require '/workspace/app/htdocs/master.inc.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/admin.lib.php';
require_once DOL_DOCUMENT_ROOT.'/comm/propal/class/propal.class.php';
if ($user->fetch('', 'admin') <= 0) throw new Exception('Missing prepared admin');
$user->loadRights();
$r=$db->query("SELECT rowid FROM ".MAIN_DB_PREFIX."propal WHERE ref_ext='interaction-39305-1'");
if (!$r) throw new Exception($db->lasterror());
$ids=[];
while ($row=$db->fetch_object($r)) $ids[]=$row->rowid;
foreach ($ids as $id) {
    $p=new Propal($db);
    if ($p->fetch($id)>0 && $p->delete($user,1)<=0) throw new Exception($p->error);
}
// Only remove the configuration created by this fixture, never an existing default.
$r=$db->query("SELECT rowid FROM ".MAIN_DB_PREFIX."const WHERE name='DISPLAY_MARK_RATES' AND entity=1 AND note='Owned by PR39305 interaction fixture'");
if (!$r) throw new Exception($db->lasterror());
if ($db->fetch_object($r) && dolibarr_del_const($db,'DISPLAY_MARK_RATES',1)<=0) throw new Exception($db->lasterror());
PHP
