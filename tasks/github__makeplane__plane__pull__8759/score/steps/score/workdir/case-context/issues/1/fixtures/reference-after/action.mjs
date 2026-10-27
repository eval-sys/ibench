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

const getBox = async (selector) => {
  const output = await command('--json', 'get', 'box', selector);
  const parsed = JSON.parse(output);
  const box = parsed.data;
  if (!box || !Number.isFinite(box.x) || !Number.isFinite(box.y)) {
    throw new Error(`Unable to resolve browser box for ${selector}`);
  }
  return box;
};

export default async function action() {
  await command('wait', '1200');
  console.log('Replay phase:', JSON.stringify({phase: 'hover', at_ms: Date.now()}));
  await command('hover', '.ProseMirror p:first-child');
  await command('wait', '400');
  const revealed = await command('eval', `(() => {
    const handle = document.querySelector('#drag-handle');
    const menu = document.querySelector('#editor-side-menu');
    return Boolean(handle && menu && getComputedStyle(handle).opacity === '1' && !menu.classList.contains('side-menu-hidden'));
  })()`);
  console.log('Handle revealed after hover:', revealed);
  // Preserve a missing handle as a recorded outcome rather than a setup failure.
  if (revealed !== 'true') return;

  const paragraph = await getBox('.ProseMirror p:first-child');
  const handle = await getBox('#drag-handle');
  const startY = Math.round(paragraph.y + paragraph.height / 2);
  const endY = Math.round(handle.y + handle.height / 2);
  const startX = Math.round(paragraph.x + paragraph.width / 2);
  const destinationX = Math.round(handle.x + handle.width / 2);
  const samples = [];
  // These reads only observe the rendered control; they never reveal or move it.
  const observe = async (x, y) => {
    const output = await command('eval', `(() => {
      const h = document.querySelector('#drag-handle');
      const m = document.querySelector('#editor-side-menu');
      const hs = getComputedStyle(h), ms = getComputedStyle(m);
      return {x:${x}, y:${y}, handleOpacity:hs.opacity, menuOpacity:ms.opacity,
        handlePointerEvents:hs.pointerEvents, menuPointerEvents:ms.pointerEvents,
        hidden:h.classList.contains('drag-handle-hidden') || m.classList.contains('side-menu-hidden'),
        overHandle:Boolean(document.elementFromPoint(${x},${y})?.closest('#drag-handle'))};
    })()`);
    samples.push(JSON.parse(output));
  };

  console.log('Replay phase:', JSON.stringify({phase: 'approach', at_ms: Date.now()}));
  let pausedInGutter = false;
  for (let x = startX; x > destinationX; x -= 2) {
    const fraction = (startX - x) / (startX - destinationX);
    const y = Math.round(startY + fraction * (endY - startY));
    await command('mouse', 'move', String(x), String(y));
    await command('wait', '60');
    if (!pausedInGutter && x < paragraph.x && x > handle.x + handle.width) {
      // A deliberate pause rules out relying on a quick dash across the gutter.
      await command('wait', '1000');
      pausedInGutter = true;
    }
    await observe(x, y);
  }
  await command('mouse', 'move', String(destinationX), String(endY));
  await command('wait', '1000');
  await observe(destinationX, endY);
  console.log('Pointer approach observations:', JSON.stringify(samples));

  // Passive event recording is diagnostic only. Input uses the built-in drag
  // command, and no DOM event, editor state, or content is synthesized here.
  await command('eval', `(() => {
    window.__caseVerifierDragEvents = [];
    document.addEventListener('dragstart', e => {
      if (e.target.closest?.('#drag-handle')) {
        window.__caseVerifierDragEvents.push({type:e.type, trusted:e.isTrusted,
          text:e.dataTransfer?.getData('text/plain')});
      }
    });
  })()`);
  const acquired = samples.at(-1);
  if (!acquired.hidden && acquired.overHandle) {
    console.log('Replay phase:', JSON.stringify({phase: 'drag', at_ms: Date.now()}));
    await command('drag', '#drag-handle', '.ProseMirror p:nth-child(2)');
    console.log('Drag initiation:', await command('eval', 'window.__caseVerifierDragEvents'));
  }
}
