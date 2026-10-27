import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);
const browser = (...args) => exec('agent-browser', args, { timeout: 60000 });
const appBase = (process.env.APP_URL || 'http://localhost:4533').replace(/\/$/, '');

export default async function setup() {
  // Prepared development admin: server/initial_setup.go and ND_DevAutoCreateAdminPassword.
  await browser('open', appBase + '/app/');
  await browser('wait', 'input[name="username"]');
  await browser('fill', 'input[name="username"]', 'admin');
  await browser('fill', 'input[name="password"]', 'admin123');
  await browser('find', 'role', 'button', 'click', '--name', 'SIGN IN', '--exact');
  await browser('wait', '--text', 'Albums');
  await browser('find', 'role', 'menuitem', 'click', '--name', 'Songs', '--exact');
  await browser('wait', '--url', appBase + '/app/#/song*');
  await browser('wait', '--text', 'Amber Waltz');
  await browser('find', 'role', 'button', 'click', '--name', 'more', '--exact');
  await browser('find', 'role', 'menuitem', 'click', '--name', 'Composer', '--exact');
  await browser('press', 'Escape');
  await browser('wait', '--fn', `getComputedStyle(document.querySelector('#long-menu')).visibility === 'hidden'`);
  await browser('find', 'role', 'columnheader', 'text', '--name', 'Composer', '--exact');
  // Expand the table so the song titles and composer names are easy to inspect.
  await browser('find', 'role', 'button', 'click', '--name', 'Close menu', '--exact');
  await browser('wait', '--fn', `document.querySelectorAll('tbody tr').length === 4 &&
    document.querySelector('[data-sort="title"].MuiTableSortLabel-active .MuiTableSortLabel-iconDirectionAsc') !== null &&
    ['Amber Waltz', 'Blue Nocturne', 'Cedar Prelude', 'Dawn Sonata'].every((title, i) => document.querySelectorAll('tbody tr')[i].textContent.includes(title)) &&
    ['Clara Vale', 'Ada Rowan', 'Dorian Lake', 'Bruno Reed'].every((composer, i) => document.querySelectorAll('tbody tr')[i].textContent.includes(composer))`);
}
