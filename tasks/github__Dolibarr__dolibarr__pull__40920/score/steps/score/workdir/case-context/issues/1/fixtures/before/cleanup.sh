#!/usr/bin/env bash
set -euo pipefail
php <<'PHP'
<?php
// Bootstrap the same native CLI environment used by scripts/product/*.php.
define('NOSESSION', 1);
require '/workspace/app/htdocs/master.inc.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/admin.lib.php';
require_once DOL_DOCUMENT_ROOT.'/product/class/product.class.php';
require_once DOL_DOCUMENT_ROOT.'/commande/class/commande.class.php';
require_once DOL_DOCUMENT_ROOT.'/expedition/class/expedition.class.php';
require_once DOL_DOCUMENT_ROOT.'/product/stock/class/entrepot.class.php';
require_once DOL_DOCUMENT_ROOT.'/product/stock/class/mouvementstock.class.php';
require_once DOL_DOCUMENT_ROOT.'/comm/action/class/actioncomm.class.php';
$langs->setDefaultLang('en_US');
$langs->loadLangs(array('main','products','sendings','agenda'));
function ok($result, $object, $operation) {
    if ($result <= 0) throw new RuntimeException($operation.': '.$object->error.' '.implode('; ', $object->errors ?? array()));
    return $result;
}
ok($user->fetch(0, 'admin'), $user, 'Resolve prepared demo admin');
$user->getrights();
// Resolve ownership by fixed keys, never by saved runtime IDs.
$shipment = new Expedition($db);
$shipmentId = 0;
if ($shipment->fetch(0, 'SH-DISPATCH') > 0) {
    $shipmentId = $shipment->id;
    ok($shipment->delete($user, 1, false), $shipment, 'Remove owned shipment');
}
$order = new Commande($db);
$orderId = 0;
if ($order->fetch(0, 'CO-DISPATCH') > 0) {
    $orderId = $order->id;
    ok($order->delete($user, 1), $order, 'Remove owned order');
}
$product = new Product($db);
$productId = 0;
if ($product->fetch(0, 'DISPATCH-LAMP') > 0) $productId = $product->id;
// Native actions can leave agenda entries after the subject has been deleted.
$where = "entity=1 AND (label LIKE '%SH-DISPATCH%' OR label LIKE '%CO-DISPATCH%'";
if ($shipmentId) $where .= " OR (elementtype='shipping' AND fk_element=".(int)$shipmentId.")";
if ($orderId) $where .= " OR (elementtype='order' AND fk_element=".(int)$orderId.")";
if ($productId) $where .= " OR (elementtype='product' AND fk_element=".(int)$productId.")";
$where .= ')';
$res = $db->query("SELECT id FROM ".MAIN_DB_PREFIX."actioncomm WHERE ".$where);
if (!$res) throw new RuntimeException($db->lasterror());
$ids = array();
while ($row = $db->fetch_object($res)) $ids[] = $row->id;
foreach ($ids as $id) {
    $event = new ActionComm($db);
    ok($event->fetch($id), $event, 'Fetch owned agenda event');
    ok($event->delete($user, 1), $event, 'Delete owned agenda event');
}
if ($productId) {
    // Remove only the isolated product's movements; Product::delete removes its stock rows.
    $res = $db->query("SELECT rowid FROM ".MAIN_DB_PREFIX."stock_mouvement WHERE fk_product=".(int)$productId);
    if (!$res) throw new RuntimeException($db->lasterror());
    $ids = array();
    while ($row = $db->fetch_object($res)) $ids[] = $row->rowid;
    foreach ($ids as $id) {
        $movement = new MouvementStock($db);
        ok($movement->fetch($id), $movement, 'Fetch owned movement');
        ok($movement->delete($user, 1), $movement, 'Delete owned movement');
    }
    ok($product->delete($user, 1), $product, 'Remove isolated product');
}
$res = $db->query("SELECT value FROM ".MAIN_DB_PREFIX."const WHERE name='REPRO_40920_STOCK_CLOSE_BACKUP' AND entity=1");
if (!$res) throw new RuntimeException($db->lasterror());
if ($row = $db->fetch_object($res)) {
    $prior = json_decode($row->value);
    if ($prior) {
        if (dolibarr_set_const($db, 'STOCK_CALCULATE_ON_SHIPMENT_CLOSE', $prior->value, $prior->type, $prior->visible, $prior->note, 1) <= 0) throw new RuntimeException('Cannot restore stock policy');
    } else {
        dolibarr_del_const($db, 'STOCK_CALCULATE_ON_SHIPMENT_CLOSE', 1);
    }
    dolibarr_del_const($db, 'REPRO_40920_STOCK_CLOSE_BACKUP', 1);
}
echo "Owned dispatch state removed; prior stock policy restored.\n";
PHP
