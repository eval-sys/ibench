import { execFile } from "node:child_process";
import { writeFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const exec = promisify(execFile);
const run = async (file, ...args) => (await exec(file, args.map(String), {
  timeout: 120_000,
  maxBuffer: 1024 * 1024,
})).stdout;
const browser = (...args) => run("agent-browser", ...args);
const read = async expression => JSON.parse(JSON.parse(await browser("eval", "JSON.stringify(" + expression + ")")));
const tabs = async () => JSON.parse(await browser("tab", "list", "--json")).data.tabs;
const state = () => read(`({
  url: location.href,
  productName: document.querySelector("input[name='name']")?.value ?? null,
  search: document.querySelector("input[placeholder='Search products...']")?.value ?? null,
  pageScroll: { x: scrollX, y: scrollY },
  gridScroll: document.querySelector(".dvn-scroller") ? {
    x: document.querySelector(".dvn-scroller").scrollLeft,
    y: document.querySelector(".dvn-scroller").scrollTop,
  } : null,
})`);

export default async function action() {
  const observations = [];
  const observe = async stage => {
    const entry = { stage, at_ms: Date.now(), tabs: await tabs(), page: await state() };
    observations.push(entry);
    console.log(JSON.stringify(entry));
  };
  const initial = await tabs();
  const catalogue = initial.find(tab => tab.active);
  await observe("initial-catalogue");
  const box = await browser("get", "box", ".dvn-scroller");
  const coordinate = name => {
    const match = box.match(new RegExp("^" + name + ":\\s*(-?[0-9.]+)", "m"));
    if (!match) throw new Error("Missing datagrid coordinate: " + name);
    return Number(match[1]);
  };
  const point = { x: Math.round(coordinate("x") + 170), y: Math.round(coordinate("y") + 61) };
  const origin = await read(`({
    x: screenX + (outerWidth - innerWidth) / 2,
    y: screenY + outerHeight - innerHeight - (outerWidth - innerWidth) / 2,
  })`);
  // Use the real window's pointer: its native menu and tab strip are recorded.
  await run("xdotool", "mousemove", "--sync", point.x + origin.x, point.y + origin.y);
  await browser("wait", "1500");
  const hit = await read(`(() => {
    const element = document.elementFromPoint(` + point.x + "," + point.y + `);
    return { tag: element?.tagName, href: element?.closest("a")?.href ?? null };
  })()`);
  observations.push({ stage: "pointer-target", at_ms: Date.now(), point, hit });
  await run("xdotool", "click", "3");
  await browser("wait", "2500");
  await observe("right-click-menu");
  await run("xdotool", "key", "--clearmodifiers", "Escape");
  await run("xdotool", "click", "2");
  // An observation window, not a success gate: retain broken/alternative outcomes.
  await browser("wait", "3000");
  const after = await tabs();
  observations.push({ stage: "middle-click-tabs", at_ms: Date.now(), tabs: after });
  const opened = after.find(tab => !initial.some(prior => prior.tabId === tab.tabId));
  if (opened) {
    // Middle-click opens a background tab; activate it in the actual browser UI.
    await run("xdotool", "key", "--clearmodifiers", "ctrl+Tab");
    await browser("tab", opened.tabId);
  }
  await browser("wait", "2500");
  await observe("page-after-middle-click");
  if (process.env.REPLAY_OUTPUT_DIRECTORY) {
    await browser("screenshot", path.join(process.env.REPLAY_OUTPUT_DIRECTORY, "opened-page.png"));
  }
  if (opened) {
    await run("xdotool", "key", "--clearmodifiers", "ctrl+shift+Tab");
    await browser("tab", catalogue.tabId);
  }
  await browser("wait", "2500");
  await observe("original-tab-after-gestures");
  if (process.env.REPLAY_OUTPUT_DIRECTORY) {
    await writeFile(path.join(process.env.REPLAY_OUTPUT_DIRECTORY, "tab-observations.json"),
      JSON.stringify({ schema_version: "browser-gestures/v1", observations }, null, 2) + "\n");
  }
}
