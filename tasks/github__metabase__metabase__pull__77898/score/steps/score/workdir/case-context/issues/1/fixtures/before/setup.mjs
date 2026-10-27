import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  return execFileAsync("agent-browser", args, {
    timeout: 60_000,
  });
}

export default async function setup() {
  await browser("open", "http://localhost:3000/auth/login");
  await browser("wait", "--text", "Sign in");
  await browser(
    "find",
    "label",
    "Email address",
    "fill",
    "repro-admin-77898@example.test",
  );
  await browser("find", "label", "Password", "fill", "ReproPass123!");
  await browser("find", "role", "button", "click", "--name", "Sign in", "--exact");
  await browser("wait", "--url", "http://localhost:3000/**");

  await browser(
    "open",
    "http://localhost:3000/collection/7789801-invite-access-demo/permissions",
  );
  await browser("wait", "--text", "Permissions for Invite Access Demo");
  await browser("wait", "--text", "Sales");
}
