import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

async function browser(...args) {
  return execFileAsync("agent-browser", args, {
    maxBuffer: 1024 * 1024,
    timeout: 30_000,
  });
}

async function waitForOutput(expected, ...args) {
  const deadline = Date.now() + 30_000;
  let actual = "";

  while (Date.now() < deadline) {
    try {
      const { stdout } = await browser(...args);
      actual = stdout.trim();
      if (actual === expected) return;
    } catch (error) {
      actual = error.stderr?.trim() || error.message;
    }
    await browser("wait", "250");
  }

  throw new Error(`Expected ${JSON.stringify(expected)}, received ${JSON.stringify(actual)}`);
}

export default async function setup() {
  await browser("open", "http://localhost:3000/");
  await browser("wait", "#email");
  await browser("fill", "#email", "editor@example.com");
  await browser("click", "button[type=\"submit\"]");
  await browser("wait", "#password");
  await browser("fill", "#password", "PlaneIssue8600!");
  await browser("click", "button[type=\"submit\"]");
  await browser("wait", "--url", "**/content-operations/**");

  await browser("open", "http://localhost:3000/content-operations/browse/EDIT-1");
  await waitForOutput("[EDIT-1:title] Prepare launch brief", "get", "value", "textarea");
  await waitForOutput(
    "[EDIT-1:desc] Outline goals for the launch and list the primary audience.",
    "get",
    "text",
    "[contenteditable=\"true\"]"
  );
  await browser("wait", "1000");
}
