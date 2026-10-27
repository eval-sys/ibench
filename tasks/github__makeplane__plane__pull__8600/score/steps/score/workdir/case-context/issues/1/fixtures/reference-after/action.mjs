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

export default async function action() {
  await waitForOutput("[EDIT-1:title] Prepare launch brief", "get", "value", "textarea");
  await waitForOutput(
    "[EDIT-1:desc] Outline goals for the launch and list the primary audience.",
    "get",
    "text",
    "[contenteditable=\"true\"]"
  );
  await browser("wait", "1500");

  await browser(
    "find",
    "role",
    "button",
    "click",
    "--name",
    "Search commands..."
  );
  await browser(
    "fill",
    "input[placeholder=\"Search commands...\"]",
    "[EDIT-2:title] Review research notes"
  );
  await waitForOutput(
    "EDIT-2\n[EDIT-2:title] Review research notes",
    "find",
    "role",
    "option",
    "text",
    "--name",
    "EDIT-2 [EDIT-2:title] Review research notes"
  );
  await browser(
    "find",
    "role",
    "option",
    "click",
    "--name",
    "EDIT-2 [EDIT-2:title] Review research notes"
  );
  await browser("wait", "--url", "**/browse/EDIT-2/");
  await waitForOutput("[EDIT-2:title] Review research notes", "get", "value", "textarea");
  await waitForOutput(
    "[EDIT-2:desc] Summarize customer interviews and capture the key findings.",
    "get",
    "text",
    "[contenteditable=\"true\"]"
  );
  await browser("wait", "1500");

  await browser(
    "find",
    "role",
    "button",
    "click",
    "--name",
    "Search commands..."
  );
  await browser(
    "fill",
    "input[placeholder=\"Search commands...\"]",
    "[EDIT-1:title] Prepare launch brief"
  );
  await waitForOutput(
    "EDIT-1\n[EDIT-1:title] Prepare launch brief",
    "find",
    "role",
    "option",
    "text",
    "--name",
    "EDIT-1 [EDIT-1:title] Prepare launch brief"
  );
  await browser(
    "find",
    "role",
    "option",
    "click",
    "--name",
    "EDIT-1 [EDIT-1:title] Prepare launch brief"
  );
  await browser("wait", "--url", "**/browse/EDIT-1/");
  await waitForOutput("[EDIT-1:title] Prepare launch brief", "get", "value", "textarea");
  await browser("wait", "1500");
}
