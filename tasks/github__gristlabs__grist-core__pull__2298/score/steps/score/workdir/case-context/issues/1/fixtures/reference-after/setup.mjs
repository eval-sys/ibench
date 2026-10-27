import { execFileSync } from 'node:child_process';
const browser = (...args) => execFileSync('agent-browser', args, { encoding: 'utf8' }).trim();

export default async function setup() {
  // The issue-owned document is shared with guests as editors by setup.sh.
  browser('open', process.env.APP_URL.replace(/\/$/, '') + '/o/docs/doc/widget-layout-page-copy');
  browser('wait', '.layout_root .test-viewsection-title');
  browser('wait', '.test-collapsed-section-title');
  // A clean guest session automatically starts the welcome tour after the view
  // is ready. Wait for it, then dismiss it with its visible close control.
  browser('wait', '.test-onboarding-close');
  browser('click', '.test-onboarding-close');
  browser('wait', '--fn', '!document.querySelector(".test-onboarding-popup")');
  browser('click', '.layout_root .test-viewsection-blank');
  if (browser('get', 'count', '.test-right-panel[data-fully-collapsed]') !== '0') {
    browser('click', '.test-right-opener');
  }
  browser('wait', '.test-right-panel[data-fully-expanded] .test-right-tab-pagewidget');
  // PagePanels.ts animates panel width for 0.4 seconds.
  browser('wait', '500');
  browser('find', 'role', 'tab', 'click', '--name', 'Table', '--exact');
  browser('wait', '.test-config-widget');
  browser('find', 'role', 'tab', 'click', '--name', 'Widget', '--exact');
  browser('wait', '.test-right-widget-title');
  if (browser('get', 'count', '.layout_root .test-viewsection-title') !== '1' ||
      browser('get', 'text', '.layout_root .active_section .test-viewsection-title') !== 'Right' ||
      browser('get', 'count', '.test-collapsed-section-title') !== '1' ||
      browser('get', 'text', '.test-collapsed-section-title') !== 'Left' ||
      browser('get', 'value', '.test-right-widget-title') !== 'Right') {
    throw new Error('Given requires active visible Right, collapsed Left, and Widget settings for Right');
  }
}
