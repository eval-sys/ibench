import { execFileSync } from 'node:child_process';
const browser = (...args) => execFileSync('agent-browser', args, { encoding: 'utf8' }).trim();

export default async function action() {
  // Step 1: present the already loaded Given, including the creator panel.
  browser('wait', '1400');

  // Step 2: duplicate this page using the visible page menu and Save button.
  browser('find', 'role', 'link', 'hover', '--name', 'O Overview', '--exact');
  browser('find', 'role', 'button', 'click', '--name', 'context menu - Overview', '--exact');
  browser('wait', '.test-docpage-duplicate');
  browser('wait', '700');
  browser('click', '.test-docpage-duplicate');
  browser('wait', '.test-modal-confirm');
  browser('wait', '900');
  browser('click', '.test-modal-confirm');
  browser('wait', '--text', 'Overview (copy)');
  browser('wait', '.test-right-widget-title');
  // Hold the resulting widgets and panel in view without changing selection.
  browser('wait', '2400');
}
