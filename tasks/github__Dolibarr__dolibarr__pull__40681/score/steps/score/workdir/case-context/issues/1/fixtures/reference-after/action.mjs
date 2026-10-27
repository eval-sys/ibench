import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
const productRow = 'tr:has(a[href="/product/stock/product.php?id=10"])';
export default async function action() {
  // Review the physical-stock row and hover its quantity, as in the original interaction.
  await browser('wait', '2000');
  const quantity = `${productRow} input[name^="tobuy"]`;
  console.log(`Displayed To order: ${(await browser('get', 'value', quantity)).stdout.trim()}`);
  await browser('hover', quantity);
  await browser('wait', '1500');
  // Allow explicitly permits help beside the quantity. Inspect this visible affordance
  // using a normal hover, without invoking tooltip code or altering page state.
  const help = `${productRow} td:has(input[name^="tobuy"]) .classfortooltip`;
  if (Number((await browser('get', 'count', help)).stdout.trim()) > 0) {
    await browser('hover', help);
    await browser('wait', '1500');
  }
  console.log((await browser('snapshot')).stdout);
}
