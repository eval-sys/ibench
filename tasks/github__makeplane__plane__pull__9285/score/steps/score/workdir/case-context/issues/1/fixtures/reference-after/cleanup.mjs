import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const command = async (...args) => {
  const { stdout, stderr } = await execFileAsync("agent-browser", args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  if (stdout) process.stdout.write(stdout);
  if (stderr) process.stderr.write(stderr);
};

export default async function cleanup() {
  await command("cookies", "clear");
  await command("open", new URL("/", process.env.APP_URL).href);
  await command("storage", "local", "clear");
  await command("storage", "session", "clear");
  await command("cookies", "clear");
}
