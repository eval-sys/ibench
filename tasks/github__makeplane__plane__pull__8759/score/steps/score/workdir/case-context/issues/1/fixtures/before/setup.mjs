import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const command = async (...args) => {
  const result = await execFileAsync('agent-browser', args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  return result.stdout.trim();
};

export default async function setup() {
  await command('open', 'http://localhost:3000/');
  await command('wait', 'input[type="email"]');
  await command('fill', 'input[type="email"]', 'editor.review@example.com');
  await command('click', 'button[type="submit"]');
  await command('wait', 'input[type="password"]');
  await command('fill', 'input[type="password"]', 'EditorHover2026!');
  await command('click', 'button[type="submit"]');
  await command('wait', '1500');

  await command(
    'open',
    'http://localhost:3000/editor-interactions/browse/CONTENT-1'
  );
  await command('wait', 'textarea[placeholder="Work item title"]');
  await command('wait', '.ProseMirror p:first-child');
  const description = await command('eval', `(() => {
    const editor = document.querySelector('.ProseMirror');
    return editor?.isContentEditable && editor.querySelectorAll('p').length >= 2;
  })()`);
  if (description !== 'true') throw new Error('Expected an editable multi-block description');
  const title = await command('get', 'value', 'textarea[placeholder="Work item title"]');
  if (title !== 'Review description blocks') throw new Error(`Unexpected work item title: ${title}`);
  await command('scrollintoview', '.ProseMirror p:first-child');
  await command('wait', '2200');
}
