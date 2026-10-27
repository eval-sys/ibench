import { execFile } from "node:child_process";
import { writeFile } from "node:fs/promises";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const browser = async (...args) => {
  const { stdout } = await execFileAsync("agent-browser", args, {
    env: process.env, maxBuffer: 1024 * 1024, timeout: 120_000,
  });
  return stdout.trim();
};
const evaluate = async expression => {
  const result = JSON.parse(await browser("--json", "eval", expression));
  if (!result.success) throw new Error(result.error);
  return result.data.result;
};

export default async function action() {
  await browser("wait", "--fn", `location.pathname === '/products/' && innerWidth === 390 && innerHeight === 844 && Boolean(document.elementFromPoint(200, 400)?.closest('.dvn-scroller'))`);
  await evaluate(`(() => {
    const state = () => ({url: location.href, pageScroll: document.scrollingElement.scrollTop,
      gridScroll: [...document.querySelectorAll('.dvn-scroller')].map(e => ({top:e.scrollTop,
        left:e.scrollLeft, height:e.clientHeight, scrollHeight:e.scrollHeight}))});
    const audit = {startedAt: Date.now(), initial: state(), events: [], state};
    window.__ibenchTouchAudit = audit;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('aria-hidden', 'true');
    svg.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:2147483647';
    const path = document.createElementNS(svg.namespaceURI, 'path');
    path.setAttribute('fill', 'none'); path.setAttribute('stroke', '#d97706'); path.setAttribute('stroke-width', '3');
    const dot = document.createElementNS(svg.namespaceURI, 'circle');
    dot.setAttribute('r', '11'); dot.setAttribute('fill', '#f59e0b55');
    dot.setAttribute('stroke', '#d97706'); dot.setAttribute('stroke-width', '2');
    svg.append(path, dot);
    let trail = '';
    const observe = event => {
      const point = event.touches?.[0] || event.changedTouches?.[0] || event;
      audit.events.push({type:event.type, at:Date.now(), trusted:event.isTrusted,
        pointerType:event.pointerType, x:point.clientX, y:point.clientY,
        target:event.target?.tagName, ...state()});
      // Inert recording annotation: draw received touch coordinates, never dispatch events.
      if (event.type === 'touchstart') { document.body.append(svg); trail = ''; }
      if (event.type.startsWith('touch') && Number.isFinite(point.clientX)) {
        trail += (trail ? ' L ' : 'M ') + point.clientX + ' ' + point.clientY;
        path.setAttribute('d', trail); dot.setAttribute('cx', point.clientX); dot.setAttribute('cy', point.clientY);
      }
      if (event.type === 'touchend' || event.type === 'touchcancel') setTimeout(() => svg.remove(), 1500);
    };
    const types = ['pointerdown','pointermove','pointerup','pointercancel','touchstart','touchmove','touchend','touchcancel','click','scroll'];
    for (const type of types) document.addEventListener(type, observe, {capture:true, passive:true});
    audit.stop = () => {
      for (const type of types) document.removeEventListener(type, observe, true);
      svg.remove();
    };
    return true;
  })()`);
  await browser("wait", "1500");
  await browser("swipe", "up", "50");
  await browser("wait", "3000");
  const observation = await evaluate(`(() => {
    const audit = window.__ibenchTouchAudit;
    const result = {startedAt:audit.startedAt, endedAt:Date.now(), gesture:{direction:'up',distance:50,start:[200,400]},
      initial:audit.initial, final:audit.state(), events:audit.events};
    audit.stop(); delete window.__ibenchTouchAudit;
    return result;
  })()`);
  console.log(JSON.stringify(observation, null, 2));
  console.log(await browser("snapshot", "-i"));
  await writeFile(new URL("../evidence/touch-gesture.json", import.meta.url), JSON.stringify(observation, null, 2) + "\n");
}
