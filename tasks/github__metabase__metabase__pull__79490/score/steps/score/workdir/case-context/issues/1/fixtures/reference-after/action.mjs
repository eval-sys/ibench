import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  const result = await execFileAsync("agent-browser", args, { timeout: 120_000 });
  return result.stdout.trim();
}

export default async function action() {
  await browser("wait", "750");
  await browser("find", "role", "button", "click", "--name", "Share");
  await browser("wait", '[role="menu"]');
  await browser("wait", "750");
  // The Definition makes invocation conditional on an executable export action.
  // Inspect the rendered control; never manufacture one when the menu omits it.
  const exportControl = '[data-testid="dashboard-export-pdf-button"]';
  const count = Number(await browser("get", "count", exportControl));
  if (!Number.isInteger(count)) throw new Error("Invalid export control count");
  if (count > 0 && await browser("is", "enabled", exportControl) === "true") {
    await browser("find", "role", "menuitem", "click", "--name", "Export as PDF");
  }
  await browser("wait", "2000");
  console.log(await browser("snapshot"));
}
