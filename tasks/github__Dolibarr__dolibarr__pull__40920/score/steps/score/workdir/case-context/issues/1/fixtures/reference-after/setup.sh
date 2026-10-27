#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"
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
// Stable account, customer and warehouse keys are shipped in the 24.0.0 demo
// selected by /opt/dev-env-profile.sh. Do not reload or replace the demo.
$soc = new Societe($db);
$res = $db->query("SELECT rowid FROM ".MAIN_DB_PREFIX."societe WHERE code_client='CU1212-0007' AND entity=1");
if (!$res || $db->num_rows($res) != 1) throw new RuntimeException('Prepared customer missing');
ok($soc->fetch($db->fetch_object($res)->rowid), $soc, 'Fetch prepared customer');
$warehouse = new Entrepot($db);
ok($warehouse->fetch(0, 'WAREHOUSEHOUSTON'), $warehouse, 'Fetch prepared warehouse');
if (getDolGlobalInt('STOCK_CALCULATE_ON_SHIPMENT') || getDolGlobalInt('STOCK_CALCULATE_ON_VALIDATE_ORDER')) throw new RuntimeException('Demo stock policy differs from its supplied definition');
// Preserve the missing stock-on-close setting across interruption and cleanup.
$name = 'STOCK_CALCULATE_ON_SHIPMENT_CLOSE';
$res = $db->query("SELECT value,type,visible,note FROM ".MAIN_DB_PREFIX."const WHERE name='".$name."' AND entity=1");
if (!$res) throw new RuntimeException($db->lasterror());
$prior = $db->fetch_object($res);
if (dolibarr_set_const($db, 'REPRO_40920_STOCK_CLOSE_BACKUP', json_encode($prior), 'chaine', 0, '', 1) <= 0) throw new RuntimeException('Cannot preserve stock policy');
if (dolibarr_set_const($db, $name, '1', 'yesno', 0, '', 1) <= 0) throw new RuntimeException('Cannot enable stock-on-close');
$conf->global->$name = '1';
$product = new Product($db);
$product->ref = 'DISPATCH-LAMP';
$product->label = 'Desk lamp';
$product->type = 0;
$product->status = 1;
$product->status_buy = 1;
$product->tobatch = 0;
$product->stockable_product = 1;
ok($product->create($user, 1), $product, 'Create isolated product');
$movement = new MouvementStock($db);
ok($movement->reception($user, $product->id, $warehouse->id, 20, 15, 'Opening stock'), $movement, 'Receive opening stock');
$order = new Commande($db);
$order->ref = 'CO-DISPATCH';
$order->ref_ext = 'customer-dispatch-40920';
$order->socid = $soc->id;
$order->date = dol_now();
ok($order->create($user, 1), $order, 'Create isolated order');
$line = ok($order->addline('Desk lamp', 25, 5, 0, 0, 0, $product->id), $order, 'Add order line');
ok($order->valid($user, 0, 1), $order, 'Validate order');
$shipment = new Expedition($db);
$shipment->ref = 'SH-DISPATCH';
$shipment->ref_ext = 'customer-dispatch-40920';
$shipment->socid = $soc->id;
$shipment->origin = 'commande';
$shipment->origin_id = $order->id;
$shipment->date_shipping = dol_now();
ok($shipment->addline($warehouse->id, $line, 5), $shipment, 'Prepare shipment line');
ok($shipment->create($user), $shipment, 'Create shipment');
ok($shipment->valid($user, 1), $shipment, 'Validate shipment');
ok($shipment->fetch($shipment->id), $shipment, 'Fetch validated shipment');
ok($shipment->setClosed(), $shipment, 'Close shipment and decrease stock');
$res = $db->query("SELECT stock FROM ".MAIN_DB_PREFIX."product WHERE rowid=".(int)$product->id);
if (!$res || (float)$db->fetch_object($res)->stock !== 15.0) throw new RuntimeException('Expected 20 minus 5 units after native close');
echo "Closed SH-DISPATCH; Desk lamp stock 15 (opening 20, shipped 5).\n";
PHP
