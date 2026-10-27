import { execFileSync } from 'node:child_process';
const browser = (...args) => execFileSync('agent-browser', args, { encoding: 'utf8' }).trim();

export default async function setup() {
  // The issue-owned document is shared with guests as editors by setup.sh.
  browser('open', 'http://localhost:8484/o/docs/doc/widget-layout-page-copy');
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
  browser('click', '.test-right-tab-pagewidget');
  browser('wait', '.test-config-widget');
  browser('click', '.test-config-widget');
  browser('wait', '.test-right-widget-title');
  if (browser('get', 'value', '.test-right-widget-title') !== 'Right') {
    throw new Error('The starting creator panel must describe the visible Right widget');
  }
}
