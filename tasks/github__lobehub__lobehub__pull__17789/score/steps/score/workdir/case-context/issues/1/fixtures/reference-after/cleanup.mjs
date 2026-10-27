import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const browser = async (...args) => {
  const { stderr, stdout } = await execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  if (stdout) process.stdout.write(stdout);
  if (stderr) process.stderr.write(stderr);
};

export default async function cleanup() {
  if (!process.env.APP_URL) throw new Error('APP_URL is required');
  await browser('open', new URL('/signin', process.env.APP_URL).href);
  await browser('cookies', 'clear');
  await browser('storage', 'local', 'clear');
  await browser('storage', 'session', 'clear');

  // agent-browser has no IndexedDB cleanup command, so clear the app's stores in-page.
  await browser(
    'eval',
    `async () => {
      const databases = await indexedDB.databases();
      for (const { name } of databases) {
        if (!name) continue;
        await new Promise((resolve, reject) => {
          const request = indexedDB.open(name);
          request.onerror = () => reject(request.error);
          request.onsuccess = () => {
            const database = request.result;
            const stores = [...database.objectStoreNames];
            if (stores.length === 0) {
              database.close();
              resolve();
              return;
            }
            const transaction = database.transaction(stores, 'readwrite');
            transaction.onerror = () => reject(transaction.error);
            transaction.oncomplete = () => {
              database.close();
              resolve();
            };
            for (const store of stores) transaction.objectStore(store).clear();
          };
        });
      }
    }`,
  );
}
