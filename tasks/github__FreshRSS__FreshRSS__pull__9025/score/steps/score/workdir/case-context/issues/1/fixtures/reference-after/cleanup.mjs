import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { access } from 'node:fs/promises';

const exec = promisify(execFile);

export default async function cleanup() {
  // Remove only the account created by the supplementary validation checks.
  const dataPath = process.env.DATA_PATH || '/var/lib/freshrss';
  if (await access(`${dataPath}/users/verifier9025`).then(() => true, () => false)) {
    await exec('php', ['/workspace/app/cli/delete-user.php', '--user', 'verifier9025'], {
      cwd: '/workspace/app', timeout: 35000,
    });
  }
  await exec('agent-browser', ['cookies', 'clear'], { timeout: 35000 });
}
