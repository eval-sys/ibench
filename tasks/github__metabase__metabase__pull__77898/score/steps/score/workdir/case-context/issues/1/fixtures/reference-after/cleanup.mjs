import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  return execFileAsync("agent-browser", args, {
    timeout: 30_000,
  });
}

export default async function cleanup() {
  await browser("cookies", "clear");

  // A newly launched browser can still be on an opaque page where Web Storage
  // is unavailable. Cookies are the only persistent authentication state.
  for (const storageType of ["local", "session"]) {
    try {
      await browser("storage", storageType, "clear");
    } catch {
      // Nothing needs clearing for this storage type on the current origin.
    }
  }
}
