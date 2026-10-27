import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);

export async function browser(...args) {
  const { stdout } = await exec('agent-browser', [...args, '--json'], {
    timeout: 90000, maxBuffer: 2 * 1024 * 1024,
  });
  const result = JSON.parse(stdout);
  if (!result.success) throw new Error(`${args[0]}: ${result.error}`);
  return result.data;
}
export function ref(snapshot, role, predicate = () => true) {
  const matches = Object.entries(snapshot.refs).filter(([, v]) => v.role === role && predicate(v.name));
  if (matches.length !== 1) throw new Error(`Expected one ${role}, found ${matches.length}`);
  return '@' + matches[0][0];
}
export async function frameSnapshot() {
  await browser('frame', 'main');
  const main = await browser('snapshot', '-i');
  await browser('frame', ref(main, 'Iframe'));
  return browser('snapshot', '-i');
}
export async function waitFrame(condition) {
  await browser('frame', 'main');
  await browser('wait', '--fn', `(() => { const d = document.querySelector('.modal.show iframe[data-testid="display-preference-iframe"]')?.contentDocument; return Boolean(d && (${condition})); })()`);
}
export async function tab(label) {
  const s = await frameSnapshot();
  const first = Object.entries(s.refs).filter(([, v]) => v.role === 'combobox').sort((a,b) => Number(a[0].slice(1))-Number(b[0].slice(1)))[0];
  await browser('select', '@' + first[0], label === 'Personal View' ? '1' : '0');
  await waitFrame(`d.querySelector('#tabspanel-select')?.selectedOptions[0]?.textContent === '${label}' && [...d.querySelectorAll('.tab-pane.active .display_preference_config')].length === 1 && d.querySelector('.tab-pane.active .select2-selection')`);
}
export async function searchComments() {
  let s = await frameSnapshot();
  // The first combobox is the tab selector; the second is the visible Select2.
  const boxes = Object.entries(s.refs).filter(([, v]) => v.role === 'combobox').sort((a,b) => Number(a[0].slice(1))-Number(b[0].slice(1)));
  if (boxes.length !== 2) throw new Error('Expected tab and add-option dropdowns');
  await browser('click', '@' + boxes[1][0]);
  s = await frameSnapshot();
  await browser('fill', ref(s, 'searchbox'), 'Comments');
  await waitFrame(`d.querySelector('.select2-search__field')?.value === 'Comments' && [...d.querySelectorAll('.select2-results__option')].some(x => x.textContent === 'Location comments')`);
}

export default async function setup() {
  await browser('open', 'http://localhost:8000/');
  await browser('wait', '#login_name');
  await browser('fill', '#login_name', 'glpi');
  await browser('fill', '#login_password', 'glpi');
  await browser('click', 'button[name="submit"]');
  await browser('wait', '--url', 'http://localhost:8000/front/central.php');
  await browser('wait', '--load', 'networkidle');
  await browser('tab', 'new', 'http://localhost:8000/front/computer.php');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--fn', `Boolean(window.jQuery?.isReady && jQuery._data(document.querySelector('.show_displaypreference_modal'), 'events')?.click)`);
  await browser('set', 'viewport', '1280', '720');
  const controls = await browser('snapshot', '-i');
  await browser('click', ref(controls, 'button', n => n === 'Select default items to show'));
  await waitFrame(`d.querySelector('#tabspanel-select') && d.querySelector('.tab-pane.active .select2-selection')`);
  await tab('Personal View');
  // Remember Personal View through the visible tab control, then reopen the
  // modal from a freshly navigated Computers page. Personal must load first:
  // the baseline updateOrder saver reads users_id from the first loaded form.
  await browser('frame', 'main');
  let main = await browser('snapshot', '-i');
  await browser('click', ref(main, 'button', n => n === 'Close'));
  await browser('wait', '--fn', `!document.querySelector('.modal.show iframe[data-testid="display-preference-iframe"]')`);
  await browser('wait', '--load', 'networkidle');
  main = await browser('snapshot', '-i');
  await browser('click', ref(main, 'link', n => n === 'Computers'));
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '--fn', `Boolean(window.jQuery?.isReady && jQuery._data(document.querySelector('.show_displaypreference_modal'), 'events')?.click)`);
  main = await browser('snapshot', '-i');
  await browser('click', ref(main, 'button', n => n === 'Select default items to show'));
  await waitFrame(`d.querySelector('#tabspanel-select')?.selectedOptions[0]?.textContent === 'Personal View' && d.querySelector('.tab-pane.active li[data-opt-id="31"]')`);
  await waitFrame(`d.querySelector('.tab-pane.active li[data-opt-id="31"]') && [...d.querySelectorAll('.display_preference_config')].length === 1 && d.querySelector('.display_preference_config input[name="users_id"]')?.value !== '0'`);
}
