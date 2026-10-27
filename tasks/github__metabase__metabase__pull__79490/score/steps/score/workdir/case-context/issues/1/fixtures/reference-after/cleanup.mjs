import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const appUrl = process.env.APP_URL;
if (!appUrl) throw new Error("APP_URL is required");

async function browser(...args) {
  await execFileAsync("agent-browser", args, { timeout: 120_000 });
}

export default async function cleanup() {
  await browser("cookies", "clear");
  await browser("open", `${appUrl}/auth/login`);
  await browser("storage", "local", "clear");
  await browser("storage", "session", "clear");
}
