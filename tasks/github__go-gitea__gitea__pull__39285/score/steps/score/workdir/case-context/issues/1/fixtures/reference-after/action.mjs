import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const exec = promisify(execFile);
const browser = async (...args) => {
  const { stdout } = await exec('agent-browser', args, { timeout: 30000 });
  if (stdout) process.stdout.write(stdout);
};

const observe = async (stage) => {
  console.log(`Observation: ${stage}`);
  await browser('get', 'url');
  await browser('snapshot', '-s', '.branch-selector-dropdown', '-i', '-u');
  await browser('eval', `JSON.stringify({
    url: location.href,
    currentRef: document.querySelector('.branch-dropdown-button')?.innerText.trim(),
    menuVisible: !!document.querySelector('.branch-selector-dropdown > .menu.visible'),
    controls: Array.from(document.querySelectorAll('.branch-tag-item')).map(el => ({
      text: el.innerText.trim(), element: el.tagName, type: el.getAttribute('type'),
      role: el.getAttribute('role'), href: el.getAttribute('href'), active: el.classList.contains('active')
    })),
    selectedRef: document.querySelector('.branch-selector-dropdown .scrolling.menu .selected')?.innerText.trim(),
    filter: document.querySelector('.branch-selector-dropdown input')?.placeholder,
    focus: document.activeElement?.getAttribute('placeholder'),
    destinations: Array.from(document.querySelectorAll('.branch-selector-dropdown a.item')).map(el => ({text: el.innerText.trim(), href: el.getAttribute('href')}))
  })`);
};

export default async function action() {
  await browser('click', '.branch-dropdown-button');
  await browser('wait', '.branch-selector-dropdown .menu.visible .item.selected');
  await observe('open selector before activation');
  await browser('hover', '.branch-tag-item.active');
  await browser('wait', '1200');
  await observe('hover over active Branches');
  await browser('click', '.branch-tag-item.active');
  await browser('wait', '1500');
  await observe('after active Branches click');
}
