import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const command = async (...args) => {
  await execFileAsync("agent-browser", args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
};

export default async function cleanup() {
  await command("open", new URL("/auth/login", process.env.APP_URL || "http://localhost:3000").href);
  await command("wait", "--load", "domcontentloaded");
  await command("storage", "local", "clear");
  await command("storage", "session", "clear");
  await command("cookies", "clear");
}
