import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  await execFileAsync("agent-browser", args, {
    maxBuffer: 1024 * 1024,
    timeout: 30_000,
  });
}

export default async function cleanup() {
  await browser("cookies", "clear");

  for (const storage of ["local", "session"]) {
    try {
      await browser("storage", storage, "clear");
    } catch {
      // A fresh browser may not have an origin whose storage can be cleared.
    }
  }
}
