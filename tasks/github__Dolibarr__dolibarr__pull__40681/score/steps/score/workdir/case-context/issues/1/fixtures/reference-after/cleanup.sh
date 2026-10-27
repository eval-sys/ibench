#!/usr/bin/env bash
set -euo pipefail
php <<'PHP'
<?php
require '/workspace/app/htdocs/master.inc.php';
require_once DOL_DOCUMENT_ROOT.'/fourn/class/fournisseur.commande.class.php';
require_once DOL_DOCUMENT_ROOT.'/societe/class/societe.class.php';
require_once DOL_DOCUMENT_ROOT.'/product/class/product.class.php';
require_once DOL_DOCUMENT_ROOT.'/comm/action/class/actioncomm.class.php';
$user = new User($db);
if ($user->fetch(0, 'admin') <= 0) throw new RuntimeException('Prepared admin missing');
$user->getrights();
$langs->loadLangs(['orders', 'stocks', 'products']);
function checked($result, $object, $operation) {
    if ($result <= 0) throw new RuntimeException($operation.': '.$object->error.' '.implode('; ', $object->errors));
}
// Resolve only this issue's order, including a partially completed setup.
$result = $db->query("SELECT rowid FROM ".MAIN_DB_PREFIX."commande_fournisseur WHERE entity=1 AND ref_supplier='RESTOCK-COMPUTERS-100'");
if (!$result) throw new RuntimeException($db->lasterror());
$ids = [];
while ($row = $db->fetch_object($result)) $ids[] = (int)$row->rowid;
foreach ($ids as $id) {
    // Native lifecycle triggers can create agenda entries linked to this order.
    $events = $db->query("SELECT id FROM ".MAIN_DB_PREFIX."actioncomm WHERE fk_element=".$id." AND elementtype='order_supplier'");
    if (!$events) throw new RuntimeException($db->lasterror());
    $eventIds = [];
    while ($row = $db->fetch_object($events)) $eventIds[] = (int)$row->id;
    foreach ($eventIds as $eventId) {
        $event = new ActionComm($db);
        checked($event->fetch($eventId), $event, 'Fetch agenda entry');
        checked($event->delete($user, 1), $event, 'Delete agenda entry');
    }
    $order = new CommandeFournisseur($db);
    checked($order->fetch($id), $order, 'Fetch owned order');
    checked($order->delete($user, 1), $order, 'Delete owned order');
}
$db->close();
PHP
