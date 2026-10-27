import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const browser = async (...args) =>
  execFileAsync("agent-browser", args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });

export default async function setup() {
  await browser("set", "viewport", "390", "844");
  await browser("open", new URL("/", process.env.APP_URL).href);
  await browser("wait", "#email");
  await browser("find", "label", "Email address", "fill", "admin@example.com");
  await browser("find", "label", "Password", "fill", "admin");
  await browser("find", "role", "button", "click", "--name", "Sign in", "--exact");
  await browser("wait", "--url", "**/home");
  await browser("wait", 'button[aria-label="Dismiss Pulse announcement"]');
  await browser(
    "find",
    "role",
    "button",
    "click",
    "--name",
    "Dismiss Pulse announcement",
    "--exact",
  );
  await browser("wait", 'button[aria-label="Open navigation"]');
  await browser("find", "role", "button", "click", "--name", "Open navigation", "--exact");
  await browser("wait", "250");
  await browser("find", "role", "link", "click", "--name", "Catalog", "--exact");
  await browser("wait", "--url", "**/products/**");
  await browser("press", "Escape");

  for (let attempt = 0; attempt < 20; attempt += 1) {
    const { stdout } = await browser("snapshot", "-i");

    if (stdout.includes("Travel Adapter") && stdout.includes("Travel Wash Bag")) {
      await browser("wait", "300");
      return;
    }

    await browser("wait", "250");
  }

  throw new Error("The fixture product rows did not become visible");
}
