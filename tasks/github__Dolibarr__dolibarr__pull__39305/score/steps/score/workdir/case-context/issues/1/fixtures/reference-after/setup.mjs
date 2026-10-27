import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
export default async function setup() {
  const appURL = process.env.APP_URL || 'http://localhost:8000';
  // Endpoint: /opt/dev-env-profile.sh and htdocs/conf/conf.php.
  // Account: dev/initdemo/README.md and its shipped SQL dump.
  await browser('open', new URL('/', appURL).href);
  await browser('fill', 'input[name="username"]', 'admin');
  await browser('fill', 'input[name="password"]', 'admin');
  await browser('click', 'input[type="submit"]');
  await browser('wait', '--load', 'networkidle');
  // Resolve the newly created draft by its stable external reference; never save IDs.
  const { stdout } = await exec('mariadb', ['-h', 'mariadb', '-u', 'dolibarr', '-plocal-development', '-N', '-B', 'dolibarr', '-e', "SELECT rowid,ref FROM llx_propal WHERE ref_ext='interaction-39305-1'"]);
  const [id, ref] = stdout.trim().split('\t');
  if (!/^\(PROV\d+\)$/.test(ref)) throw new Error('Isolated proposal missing');
  await browser('open', new URL('/comm/propal/list.php', appURL).href);
  await browser('fill', 'input[name="search_ref"]', ref);
  await browser('press', 'Enter');
  await browser('wait', '--load', 'networkidle');
  await browser('wait', '500');
  await browser('click', `a[href="/comm/propal/card.php?id=${id}&save_lastsearch_values=1"]`);
  await browser('wait', 'a:has(.clickmarkforalllines)');
  await browser('scroll', 'down', '380');
  await browser('scroll', 'right', '280');
  await browser('wait', '500');
}
