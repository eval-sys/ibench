#!/usr/bin/env bash
set -euo pipefail
# Idempotent even when called without a preceding runner cleanup.
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"
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
// /opt/dev-env-profile.sh loads the shipped 24.0.0 demo and upgrades it.
// Its dump fixes COMP-XP4523 at stock 110, desired 200, alert 150,
// and supplier Teclib at code SU1108-0001. Reuse them without updates.
$product = new Product($db);
checked($product->fetch(0, 'COMP-XP4523'), $product, 'Fetch prepared product');
$supplierResult = $db->query("SELECT rowid FROM ".MAIN_DB_PREFIX."societe WHERE entity=1 AND code_fournisseur='SU1108-0001' AND fournisseur=1");
$supplier = $supplierResult ? $db->fetch_object($supplierResult) : null;
if (!$supplier) throw new RuntimeException('Prepared Teclib supplier missing');
$order = new CommandeFournisseur($db);
$order->socid = (int)$supplier->rowid;
$order->fourn_id = $order->socid;
$order->ref_supplier = 'RESTOCK-COMPUTERS-100';
$order->note_private = 'Computer replenishment: 100 units awaiting delivery.';
$order->date = dol_now();
checked($order->create($user), $order, 'Create purchase order');
checked($order->addline('Computer XP4523', 400, 100, 20, 0, 0, $product->id, 0, 'COMP-XP4523'), $order, 'Add 100 computers');
// Fetch loads the complete lines before the native validation checks.
checked($order->fetch($order->id), $order, 'Fetch purchase order');
checked($order->valid($user), $order, 'Validate purchase order');
checked($order->approve($user), $order, 'Approve purchase order');
checked($order->commande($user, dol_now(), 0), $order, 'Mark purchase order sent');
$db->close();
PHP
