import { browser, ref, frameSnapshot, waitFrame, tab, searchComments } from './setup.mjs';

async function selectComments() {
  // Select2's nested options lack snapshot refs. Read the visible exact label,
  // then click its actual control; do not assume an option position.
  const { result: id } = await browser('eval', `(() => {
    const d = document.querySelector('.modal.show iframe').contentDocument;
    const matches = [...d.querySelectorAll('.select2-results__option[role="option"]')].filter(e => e.textContent.trim() === 'Comments');
    if (matches.length !== 1) throw new Error('Expected one ordinary Comments option');
    return matches[0].id;
  })()`);
  await browser('click', '#' + id);
}

export default async function action() {
  // 1. Present the personal list already established by setup (Status selected).
  await browser('wait', '1800');

  // 2. Select Comments in the personal view and add it to that list.
  // Global View is unopened here: the baseline saver reads the first loaded
  // form's users_id, so loading both forms before Add would also write globals.
  await searchComments();
  await browser('wait', '1200');
  let s = await frameSnapshot();
  await selectComments();
  await waitFrame(`d.querySelector('.tab-pane.active select[name="num"]')?.value === '16'`);
  await browser('wait', '900');
  s = await frameSnapshot();
  await browser('click', ref(s, 'button', n => /Add$/.test(n)));
  await waitFrame(`d.querySelector('.tab-pane.active li[data-opt-id="16"]') && d.defaultView.jQuery.active === 0`);
  await browser('wait', '2000');

  // 3. Load Global View alongside the personal form and inspect the same field.
  await tab('Global View');
  await browser('wait', '1600');
  await searchComments();
  await browser('wait', '2200');
  await browser('frame', 'main');
  console.log('Global search after personal addition:', await browser('eval', `document.querySelector('.modal.show iframe').contentDocument.querySelector('.select2-results').innerText`));
}
