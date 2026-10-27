import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  await execFileAsync("agent-browser", args, { timeout: 120_000 });
}

export default async function setup() {
  await browser("open", "http://localhost:3000/auth/login");
  await browser("wait", "--text", "Sign in to Metabase");
  await browser(
    "find",
    "label",
    "Email address",
    "fill",
    "lobebench.pr79490@example.com",
  );
  await browser(
    "find",
    "label",
    "Password",
    "fill",
    "Repro-79490-Pdf!",
  );
  await browser("find", "role", "button", "click", "--name", "Sign in");
  await browser("wait", "--url", "http://localhost:3000/");
  await browser("wait", "--text", "Search");
  await browser("wait", "1000");

  await browser("open", "http://localhost:3000/dashboard/7949001");
  await browser("wait", "--text", "This dashboard is empty");
}
