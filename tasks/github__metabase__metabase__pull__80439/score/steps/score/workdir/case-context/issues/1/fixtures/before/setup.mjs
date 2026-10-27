import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  const { stdout } = await execFileAsync("agent-browser", args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  return stdout.trim();
}

export default async function setup() {
  await browser("open", `${process.env.APP_URL}/auth/login`);
  await browser("wait", 'input[name="username"]');
  await browser(
    "fill",
    'input[name="username"]',
    process.env.DEV_ENV_ADMIN_EMAIL,
  );
  await browser("fill", 'input[name="password"]', process.env.DEV_ENV_ADMIN_PASSWORD);
  await browser("click", 'button[type="submit"]');
  await browser("wait", "--url", "**/");

  await browser("open", `${process.env.APP_URL}/collection/root`);
  await browser("wait", 'a[href^="/question/"]');
  await browser(
    "find",
    "text",
    "PR 80439 Alert Target Check",
    "click",
  );
  await browser("wait", 'button[aria-label^="Move, trash"]');

  const snapshot = await browser("snapshot", "-i", "-c");
  if (snapshot.includes('button "Start exploring"')) {
    await browser(
      "find",
      "role",
      "button",
      "click",
      "--name",
      "Start exploring",
      "--exact",
    );
  }

  await browser("wait", 'button[aria-label^="Move, trash"]');
  await browser("wait", "600");
}
