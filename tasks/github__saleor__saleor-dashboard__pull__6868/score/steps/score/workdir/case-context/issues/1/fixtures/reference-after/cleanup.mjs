import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const command = (...arguments_) =>
  execFileAsync("agent-browser", arguments_, {
    timeout: 30_000,
    maxBuffer: 1024 * 1024,
  });

export default async function cleanup() {
  await command("cookies", "clear").catch(() => undefined);
  await command("storage", "local", "clear").catch(() => undefined);
  await command("storage", "session", "clear").catch(() => undefined);
}
