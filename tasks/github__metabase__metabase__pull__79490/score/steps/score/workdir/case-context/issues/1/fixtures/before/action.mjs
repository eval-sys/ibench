import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  await execFileAsync("agent-browser", args, { timeout: 120_000 });
}

export default async function action() {
  await browser("wait", "750");
  await browser("find", "role", "button", "click", "--name", "Share");
  await browser("wait", "--text", "Export as PDF");
  await browser("wait", "750");
  await browser(
    "find",
    "role",
    "menuitem",
    "click",
    "--name",
    "Export as PDF",
  );
  await browser("wait", "--text", "Download completed");
}
