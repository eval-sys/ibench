import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  await execFileAsync("agent-browser", args, { timeout: 120_000 });
}

export default async function cleanup() {
  await browser("cookies", "clear");
  await browser("open", "http://localhost:3000/auth/login");
  await browser("storage", "local", "clear");
  await browser("storage", "session", "clear");
}
