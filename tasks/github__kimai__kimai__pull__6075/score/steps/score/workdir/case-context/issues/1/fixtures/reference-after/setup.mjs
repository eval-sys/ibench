import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const appURL = (process.env.APP_URL || 'http://localhost:8000').replace(/\/$/, '');
async function browser(...args) {
  const { stdout } = await exec('agent-browser', args, { timeout: 120000 });
  return stdout.trim();
}

export default async function setup() {
  // /opt/dev-env-profile.sh documents this endpoint and loads UserFixtures.
  // UserFixtures defines this prepared account and its password.
  await browser('open', `${appURL}/en/login`);
  await browser('fill', '#username', 'super_admin');
  await browser('fill', '#password', 'password');
  await browser('find', 'role', 'button', 'click', '--name', 'Log in');
  await browser('wait', '--load', 'networkidle');

  // Fresh development databases show the supported onboarding flow.
  // Follow it if present; do not alter the global wizard configuration.
  if (await browser('get', 'url') === `${appURL}/en/wizard/intro`) {
    await browser('find', 'text', 'Next', 'click', '--exact');
    await browser('wait', '--url', `${appURL}/en/wizard/profile`);
  }
  if (await browser('get', 'url') === `${appURL}/en/wizard/profile`) {
    await browser('find', 'role', 'button', 'click', '--name', 'Next');
    await browser('wait', '--url', `${appURL}/en/wizard/finish`);
  }
  if (await browser('get', 'url') === `${appURL}/en/wizard/finish`) {
    await browser('find', 'text', 'Next', 'click', '--exact');
    await browser('wait', '--load', 'networkidle');
  }
  await browser('find', 'role', 'link', 'click', '--name', 'My times');
  await browser('wait', '--url', `${appURL}/en/timesheet/`);
  await browser('wait', '--load', 'networkidle');
  await browser('click', '#search-dropdown-btn');

  async function choose(field, name) {
    await browser('fill', `#${field}-ts-control`, name);
    await browser('find', 'role', 'option', 'click', '--name', name, '--exact');
    await browser('wait', '--load', 'networkidle');
  }
  await choose('customers', 'Northwind Studio');
  await choose('customers', 'Eastwood Design');
  await choose('projects', 'Brand planning');
  await choose('projects', 'Website design');
  await choose('projects', 'Content review');
  // Blur the option picker without closing or submitting the search filter.
  await browser('focus', '#search-dropdown-btn');
  await browser('wait', '--fn', `
    JSON.stringify([...document.querySelector('#customers').selectedOptions].map(o => o.textContent.trim()).sort()) === JSON.stringify(['Eastwood Design', 'Northwind Studio']) &&
    JSON.stringify([...document.querySelector('#projects').selectedOptions].map(o => o.textContent.trim()).sort()) === JSON.stringify(['Brand planning', 'Content review', 'Website design']) &&
    document.querySelector('#search-dropdown-btn').getAttribute('aria-expanded') === 'true'
  `);
  console.log('Given selections:', await browser('eval', `JSON.stringify(['customers', 'projects'].map(id => ({field: id, selected: [...document.getElementById(id).selectedOptions].map(o => ({id: o.value, label: o.textContent.trim()})), visible: [...document.getElementById(id).nextElementSibling.querySelectorAll('.ts-control .item')].map(e => e.textContent.trim())})))`));
}
