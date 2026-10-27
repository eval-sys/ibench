import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const command = (...arguments_) =>
  execFileAsync('agent-browser', arguments_, {
    env: process.env,
    timeout: 120_000,
  });

export default async function setup() {
  await command('open', 'http://localhost:3000/#/auth/login');
  await command('wait', '--text', 'Log into my account');
  await command('find', 'placeholder', 'Work email', 'fill', 'layer-navigation-case@example.com');
  await command('find', 'placeholder', 'Password', 'fill', 'LayerNavigation123!');
  await command('find', 'role', 'button', 'click', '--name', 'CONTINUE', '--exact');
  await command('wait', '--url', '**/#/dashboard/**');

  await command(
    'open',
    'http://localhost:3000/#/workspace?team-id=8a114270-0000-4000-8000-000000000010&file-id=8a114270-0000-4000-8000-000000000001&page-id=8a114270-0000-4000-8000-000000000002',
  );
  await command('wait', '--text', 'Layer Navigation Study');
  await command('press', 'Control+h');
  await command('wait', '--text', 'Layer names');
  await command('find', 'placeholder', 'Find…', 'fill', 'Waypoint');
  await command('find', 'text', 'Layer names', 'click');
  await command('wait', '--text', '1 / 40');
  await command('wait', '700');
}
