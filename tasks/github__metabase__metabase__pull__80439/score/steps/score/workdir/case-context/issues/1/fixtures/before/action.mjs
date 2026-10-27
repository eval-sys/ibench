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

const removeRecipient = '[data-testid="token-field"] button[aria-label="Remove"]';
const sendNow = '[data-testid="alert-create"] button[data-variant="outline"]';

export default async function action() {
  await browser("click", 'button[aria-label^="Move, trash"]');
  await browser("wait", "--text", "Create an alert");
  await browser("find", "role", "menuitem", "click", "--name", "Create an alert");
  await browser("wait", '[role="dialog"]');
  await browser("wait", removeRecipient);
  if (await browser("get", "count", removeRecipient) !== "1") {
    throw new Error("Given requires exactly one default email recipient");
  }
  await browser("wait", `${sendNow}:not([disabled])`);
  await browser("scrollintoview", sendNow);
  console.log("Before removing the sole recipient:\n" + await browser("snapshot", "-i", "-c"));
  await browser("wait", "900");

  // The user's removal goes through the visible recipient control.
  await browser("click", removeRecipient);
  await browser("wait", 'input[placeholder="Enter user names or email addresses"]');
  if (await browser("get", "count", removeRecipient) !== "0") {
    throw new Error("The email recipient field is not empty");
  }
  await browser("scrollintoview", sendNow);
  // Observe the result without requiring the repair to have succeeded.
  await browser("wait", "1200");
  console.log("Send now enabled after recipient removal:", await browser("is", "enabled", sendNow));
  console.log("After removing the sole recipient:\n" + await browser("snapshot", "-i", "-c"));
}
