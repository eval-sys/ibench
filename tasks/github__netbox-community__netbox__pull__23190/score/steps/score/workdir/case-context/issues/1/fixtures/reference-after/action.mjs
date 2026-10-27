import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => {
  const result = await exec('agent-browser', args, { timeout: 60000, maxBuffer: 1024 * 1024 });
  if (result.stdout) process.stdout.write(result.stdout);
  return result;
};
const pause = () => browser('wait', '2500');
// Read-only runtime evidence: no event injection or state mutation.
const inspect = label => {
  console.log(`\n${label}`);
  return browser('eval', `Array.from(document.querySelectorAll('table.object-list tbody tr')).map(r => ({cells:Array.from(r.cells).map(c=>c.innerText),links:Array.from(r.querySelectorAll('a[href]')).filter(a=>a.getAttribute('href')!=='#').map(a=>({text:a.innerText,href:a.getAttribute('href')}))}))`);
};

export default async function action() {
  await browser('wait', '4000');
  await inspect('Starting filtered catalog');
  await pause();
  await browser('find', 'role', 'link', 'click', '--name', 'Module Bay Types', '--exact');
  await browser('wait', '--text', 'SFP28 transceiver bay');
  await browser('find', 'role', 'link', 'click', '--name', 'SFP28 transceiver bay', '--exact');
  await browser('wait', '--text', 'Compatible Module Types');
  await browser('wait', 'table.object-list tbody a[href^="/dcim/module-types/"]');
  await inspect('Compatible collection and distinct manufacturers');
  await pause();

  // Click the visible table headings. Their accessible names gain arrow icons
  // when sorted, and the navigation has a similarly named Manufacturers link.
  await browser('click', 'table.object-list th:nth-child(3) > a[hx-get^="/dcim/module-types/"]');
  await browser('wait', 'table.object-list th.asc a[hx-get*="sort=-manufacturer"]');
  await pause();
  await inspect('After first Manufacturer heading click');
  await browser('click', 'table.object-list th:nth-child(3) > a[hx-get^="/dcim/module-types/"]');
  await browser('wait', 'table.object-list th.desc a[hx-get*="sort=manufacturer"]');
  await pause();
  await inspect('After second Manufacturer heading click');
  await browser('click', 'table.object-list th:nth-child(1) > a[hx-get^="/dcim/module-types/"]');
  await browser('wait', 'table.object-list th.asc a[hx-get*="sort=-model"]');
  await pause();
  await inspect('Model ascending');

  // Inspect the collection's browsing menu and choose its smallest visible
  // bound. This retains all 38 assignments and exercises every page.
  await browser('find', 'role', 'button', 'click', '--name', 'Per Page');
  await browser('find', 'role', 'link', 'click', '--name', '25', '--exact');
  await browser('wait', '--text', 'Showing 1-25 of 38');
  await pause();
  await inspect('First bounded page');
  await browser('find', 'role', 'link', 'click', '--name', 'Next page', '--exact');
  await browser('wait', '--text', 'Showing 26-38 of 38');
  await browser('scroll', 'up', '4000');
  await pause();
  await inspect('Remaining compatible types');

  // Review the lower bay information, then return to the collection beginning.
  await browser('scroll', 'down', '1000');
  await pause();
  await browser('find', 'role', 'heading', 'text', '--name', 'Module Bays', '--exact');
  await browser('find', 'role', 'link', 'click', '--name', 'Page 1', '--exact');
  await browser('wait', '--text', 'Showing 1-25 of 38');
  await browser('scroll', 'up', '4000');
  await pause();
  await browser('snapshot');
}
