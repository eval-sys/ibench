import { execFile } from 'node:child_process';
import { rm } from 'node:fs/promises';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const csvPath = '/tmp/actual-pr-7827-import-settings.csv';

async function command(...args) {
  return execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
}

export default async function cleanup() {
  await rm(csvPath, { force: true });

  // Use a same-origin non-app document so no open Actual connection can block
  // deletion of the IndexedDB databases owned by this browser fixture.
  await command('open', 'http://localhost:3210/favicon.ico');
  await command('wait', '--load', 'domcontentloaded');
  await command(
    'eval',
    `(async () => {
      localStorage.clear();
      sessionStorage.clear();
      const databases = await indexedDB.databases();
      await Promise.all(databases.filter(database => database.name).map(database =>
        new Promise((resolve, reject) => {
          const request = indexedDB.deleteDatabase(database.name);
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
          request.onblocked = () => reject(new Error('IndexedDB deletion blocked: ' + database.name));
        })
      ));
    })()`,
  );
}
