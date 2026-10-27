import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const appUrl = process.env.APP_URL;
if (!appUrl) throw new Error("APP_URL is required");

async function browser(...args) {
  await execFileAsync("agent-browser", args, { timeout: 120_000 });
}

export default async function setup() {
  await browser("open", `${appUrl}/auth/login`);
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
  await browser("wait", "--url", `${appUrl}/`);
  await browser("wait", "--text", "Search");
  await browser("wait", "1000");

  await browser("open", `${appUrl}/dashboard/7949001`);
  await browser("wait", "--text", "This dashboard is empty");
}
