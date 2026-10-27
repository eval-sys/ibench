import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const run = async (...args) => {
  const { stdout } = await execFileAsync('agent-browser', args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  return stdout.trim();
};

const fileSelector = '[role="button"][aria-label="Inspect Save Study"]';


// Read-only diagnostics: use the product's exported debug reader; do not
// dispatch events, alter document data, or replace the UI interaction.
const stateProbe = `(() => {
  const read = path => {
    let value; const original = console.log;
    try { console.log = x => { value = x; }; debug.get_state(path); }
    finally { console.log = original; }
    return value;
  };
  const p = read(':persistence');
  let rectangle = null;
  try { rectangle = debug.dump_object('Rectangle'); } catch (_) { /* absent in the empty snapshot */ }
  return {at: Date.now(), persistence: p && {status: p.status,
    queue: p.queue?.map(id => id.uuid),
    commits: Object.values(p.index || {}).map(c => ({id: c.id?.uuid,
      changes: c.changes?.map(x => ({type: x.type, id: x.id?.uuid,
        name: x.obj?.name, width: x.obj?.width, height: x.obj?.height}))})),
    error: p.error && {code: p.error.code, type: p.error.type, causeType: p.error['cause-type'], hint: p.error.hint}},
    global: read(':workspace-global'),
    rectangle: rectangle && {id: rectangle.id?.uuid, name: rectangle.name, width: rectangle.width, height: rectangle.height},
    statusTitle: document.querySelector('[class*=status-notification]')?.title};
})()`;
const observe = async label => {
  const value = JSON.parse(await run('eval', stateProbe));
  console.log(label, JSON.stringify(value, null, 2));
  return value;
};

export default async function action() {
  // Recording restarts the page; wait for the workspace to settle before input.
  await run('wait', 'button[aria-label="Rectangle (R)"]');
  await run('wait', '1500');
  await run('click', 'button[aria-label="Rectangle (R)"]');
  await run('wait', '1000');
  await run('mouse', 'move', '500', '190');
  await run('mouse', 'down');
  await run('mouse', 'move', '650', '300');
  await run('mouse', 'up');
  await run('wait', '1300');
  await run('wait', '[title="Saving"]');
  const pending = await observe('pending edit before transition');
  if (!pending.rectangle || !['pending', 'saving'].includes(pending.persistence?.status)) {
    throw new Error('Given not established: completed rectangle edit must still be awaiting persistence');
  }

  await run('find', 'role', 'tab', 'click', '--name', 'INSPECT');
  await run('wait', '--text', 'Inspecting code (View Only)');
  await observe('Inspect entered');
  await run('wait', '3800');
  await observe('Inspect after autosave');
  console.log(await run('network', 'requests', '--filter', 'update-file', '--json'));

  await run('click', 'a[class*="main-icon"]');
  await run('wait', '[data-testid="dashboard-files-layout-list"]');
  await run('click', '[data-testid="dashboard-files-layout-list"]');
  await run('wait', fileSelector);
  await run('dblclick', fileSelector);
  await run('wait', 'button[aria-label="Rectangle (R)"]');
  await run('wait', '1200');
  await observe('reopened file');
}

