import { execFile, spawn } from 'node:child_process';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const run = async (...args) => (await execFileAsync('agent-browser', args, {
  maxBuffer: 1024 * 1024, timeout: 120_000,
})).stdout.trim();

// Read only: no dispatch, document mutation, or replacement of user input.
// Debug availability is diagnostic, never a requirement for a valid capture.
const readState = () => {
  const result = { at_ms: Date.now(), url: location.href };
  const status = document.querySelector('[class*=status-notification]');
  result.status = status && { title: status.title, text: status.innerText };
  result.visible_text = document.body.innerText;
  try {
    const read = key => {
      let value;
      const original = console.log;
      try { console.log = x => { value = x; }; debug.get_state(key); }
      finally { console.log = original; }
      return value;
    };
    const p = read(':persistence');
    const g = read(':workspace-global');
    result.persistence = p == null ? null : {
      status: p.status,
      queue: (p.queue || []).map(id => id.uuid),
      commits: Object.values(p.index || {}).map(c => ({
        id: c.id?.uuid,
        changes: (c.changes || []).map(x => ({
          type: x.type, id: x.id?.uuid, name: x.obj?.name,
          width: x.obj?.width, height: x.obj?.height,
        })),
      })),
      error: p.error && { code: p.error.code, type: p.error.type },
    };
    result.workspace = { read_only: g?.['read-only?'], preview_id: g?.['preview-id']?.uuid };
    let rectangle = null;
    try { rectangle = debug.dump_object('Rectangle'); } catch (_) { /* empty snapshot */ }
    result.rectangle = rectangle && {
      id: rectangle.id?.uuid, name: rectangle.name,
      width: rectangle.width, height: rectangle.height,
    };
  } catch (_) { result.diagnostic_unavailable = true; }
  return result;
};

export default async function action() {
  const evidence = {
    schema_version: 'history-save-observations/v1',
    scope: 'Same-run read-only diagnostics; no additional scoring requirement.',
    samples: [], timing: [],
  };
  const mark = label => evidence.timing.push({ label, at_ms: Date.now() });
  const observe = async label => {
    try {
      const sample = JSON.parse(await run('eval', '(' + readState.toString() + ')()'));
      evidence.samples.push({ label, ...sample });
    } catch (_) { evidence.samples.push({ label, at_ms: Date.now(), diagnostic_unavailable: true }); }
  };
  let blocker;
  let completed;
  try {
    await run('wait', 'button[aria-label="Rectangle (R)"]');
    await run('wait', '1500');
    await observe('initial');
    const database = new URL(process.env.PENPOT_DATABASE_URI);
    blocker = spawn('psql', ['-X', '-h', database.hostname, '-U', process.env.PENPOT_DATABASE_USERNAME,
      '-d', database.pathname.slice(1), '-v', 'ON_ERROR_STOP=1'],
      { env: { ...process.env, PGPASSWORD: process.env.PENPOT_DATABASE_PASSWORD } });
    completed = new Promise(resolve => {
      blocker.on('error', () => resolve(false));
      blocker.on('exit', code => { mark('database lock released'); resolve(code === 0); });
    });
    const acquired = new Promise((resolve, reject) => {
      let output = '';
      blocker.stdout.on('data', chunk => {
        output += chunk;
        if (output.includes('LOCK TABLE')) resolve();
      });
      blocker.on('error', reject);
      blocker.on('exit', () => reject(new Error('save delay exited before lock confirmation')));
    });
    blocker.stdin.end('BEGIN;\nLOCK TABLE file IN SHARE MODE;\nSELECT pg_sleep(12);\nCOMMIT;\n');
    await acquired;
    mark('database lock acquired');
    await run('click', 'button[aria-label="Rectangle (R)"]');
    await run('wait', '1000');
    await run('mouse', 'move', '500', '190');
    await run('mouse', 'down');
    await run('mouse', 'move', '650', '300');
    await run('mouse', 'up');
    mark('rectangle drawn');
    await run('wait', '1300');
    await observe('pending edit');
    // Request preview before the normal 3s autosave debounce elapses.
    // The database delay stays identical on both revisions.
    await run('find', 'role', 'button', 'click', '--name', 'History');
    await run('wait', '[aria-label="Open version menu"]');
    await run('click', '[aria-label="Open version menu"]');
    await observe('before preview request');
    mark('preview requested');
    await run('find', 'role', 'button', 'click', '--name', 'Preview version');
    // Fixed observation window accepts immediate preview or saving first.
    // Never wait for the reference title/status/queue as a success gate.
    await observe('after preview request');
    await run('wait', '3800');
    await observe('past autosave interval');
    if (!await completed) throw new Error('database save-delay fixture failed');
    // Also leave room for implementations that save before displaying preview.
    await run('wait', '4500');
    await observe('after database release');
    const exitVisible = JSON.parse(await run('eval',
      'Array.from(document.querySelectorAll("button")).some(b => b.textContent.trim().toUpperCase() === "EXIT")'));
    if (exitVisible) {
      await run('find', 'role', 'button', 'click', '--name', 'EXIT');
      await run('wait', '900');
    }
    await observe('live file after exit attempt');
    await run('click', 'a[class*="main-icon"]');
    await run('wait', '[data-testid="dashboard-files-layout-list"]');
    await run('click', '[data-testid="dashboard-files-layout-list"]');
    const fileSelector = '[role="button"][aria-label="Version Preview Study"]';
    await run('wait', fileSelector);
    await run('dblclick', fileSelector);
    await run('wait', 'button[aria-label="Rectangle (R)"]');
    await run('wait', '1200');
    await observe('reopened file');
    try { evidence.requests = JSON.parse(await run('network', 'requests', '--filter', 'update-file', '--json')); }
    catch (_) { evidence.requests_unavailable = true; }
  } finally {
    if (blocker && blocker.exitCode === null) blocker.kill('SIGTERM');
    if (completed) await completed;
    await writeFile(path.join(process.env.REPLAY_OUTPUT_DIRECTORY, 'save-observations.json'),
      JSON.stringify(evidence, null, 2) + '\n');
    console.log(JSON.stringify(evidence, null, 2));
  }
}
