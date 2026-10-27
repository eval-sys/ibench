import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export default async function cleanup() {
  await execFileAsync("agent-browser", ["cookies", "clear"], {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
}
