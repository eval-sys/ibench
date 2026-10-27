import { execFileSync } from 'node:child_process';
const browser = (...args) => execFileSync('agent-browser', args, { encoding: 'utf8' }).trim();

export default async function action() {
  // Step 1: present the already loaded Given, including the creator panel.
  browser('wait', '1400');
  console.log('Given:', browser('get', 'text', '.layout_root .active_section .test-viewsection-title'),
    'active;', browser('get', 'text', '.test-collapsed-section-title'), 'collapsed; panel title',
    browser('get', 'value', '.test-right-widget-title'));
  const originalSection = browser('get', 'attr', '.layout_root .active_section', 'class');

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
  browser('wait', '--url', '**/p/*');
  browser('wait', '.test-right-widget-title');
  // Hold the resulting widgets and panel in view without changing selection.
  browser('wait', '2400');
  console.log('After Save:', browser('get', 'url'));
  console.log('Visible widget count:', browser('get', 'count', '.layout_root .test-viewsection-title'));
  console.log('Active widget:', browser('get', 'text', '.layout_root .active_section .test-viewsection-title'));
  console.log('Collapsed widget count:', browser('get', 'count', '.test-collapsed-section-title'));
  console.log('Collapsed widget:', browser('get', 'text', '.test-collapsed-section-title'));
  console.log('Open creator panel title:', browser('get', 'value', '.test-right-panel[data-fully-expanded] .test-right-widget-title'));
  console.log('Original widget element:', originalSection);
  console.log('Copied widget element:', browser('get', 'attr', '.layout_root .active_section', 'class'));
}
