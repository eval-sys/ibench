import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const execute = promisify(execFile);
async function browser(...args) {
  const { stdout } = await execute('agent-browser', args, { timeout: 60000, maxBuffer: 1024 * 1024 });
  return stdout.trim();
}

async function hold() {
  await browser('wait', '1600');
  // A read-only screenshot keeps the installed recorder sampling each stable state.
  // Without this, replay.webm stopped updating before the deletion confirmation.
  await browser('screenshot', '/tmp/shipment-delete-stock-state.png');
}
const link = name => browser('find', 'role', 'link', 'click', '--name', name, '--exact');
async function showMovements() {
  await link('Full list');
  await browser('wait', 'input[name="search_product_ref"]');
  await browser('wait', '--text', 'Opening stock');
  await browser('scroll', 'right', '800');
  await hold();
}
export default async function action() {
  // 1. Present the stock page already established by setup.
  await hold();

  // 2. Follow the product's stock history, exposing its quantity and Origin columns.
  await showMovements();

  // 3. Follow this movement's source shipment and present its Processed status.
  await link('SH-DISPATCH');
  await browser('wait', 'a.butActionDelete');
  await browser('wait', '--text', 'Processed');
  await browser('scroll', 'up', '1500');
  await hold();

  // 4. Inspect the warning and explicitly choose not to restore stock.
  await link('DELETE');
  await browser('wait', '#alsoUpdateStock');
  console.log(`Restoration default (not a pass condition): ${await browser('is', 'checked', '#alsoUpdateStock')}`);
  console.log(`Deletion confirmation: ${await browser('get', 'text', 'body')}`);
  await browser('uncheck', '#alsoUpdateStock');
  await hold();

  // 5. Confirm deletion and present the shipment overview returned by the application.
  await browser('find', 'role', 'button', 'click', '--name', 'Yes', '--exact');
  await browser('wait', '--url', '**/expedition/index.php');
  await browser('wait', '--text', 'Latest shipments');
  await hold();

  // 6. Follow the product from the product overview's recent movements, then its Stock tab.
  await link('Products | Services');
  await browser('wait', '--text', 'Latest 3 stock movements');
  const snapshot = await browser('snapshot', '-i');
  const productLink = snapshot.match(/- link " DISPATCH-LAMP" \[ref=(e\d+)\]/);
  if (!productLink) throw new Error('Desk lamp link missing from recent stock movements');
  await browser('click', '@' + productLink[1]);
  await browser('wait', 'a[href*="/product/stock/product.php"]');
  await link('Stock');
  await browser('wait', '--text', 'Physical Stock');
  await browser('wait', 'a[href*="movement_list.php?idproduct="]');
  await hold();

  // 7. Revisit the product's movement history and present the remaining movement and Origin cell.
  await showMovements();
}
