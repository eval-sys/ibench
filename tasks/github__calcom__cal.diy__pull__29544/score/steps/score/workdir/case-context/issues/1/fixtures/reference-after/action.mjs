import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const command = async (...args) => {
  const result = await execFileAsync("agent-browser", args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  if (result.stdout) process.stdout.write(result.stdout);
};

async function observe(state, oldPassword, newPassword) {
  // Verify the entered scenario, then observe validity without assuming a repair.
  await command("wait", "--fn", `(() => {
    const oldPassword = document.querySelector("input[name='oldPassword']");
    const newPassword = document.querySelector("input[name='newPassword']");
    return oldPassword?.value === ${JSON.stringify(oldPassword)} &&
      newPassword?.value === ${JSON.stringify(newPassword)} && newPassword?.type === "text";
  })()`);
  // Leave a bounded viewing window for validation feedback and the recording.
  await command("wait", "1200");
  console.log("Password form state:", state);
  await command("snapshot");
  await command("eval", `JSON.stringify({
    state: ${JSON.stringify(state)},
    oldPasswordFilled: document.querySelector("input[name='oldPassword']").value.length > 0,
    newPassword: document.querySelector("input[name='newPassword']").value,
    newPasswordType: document.querySelector("input[name='newPassword']").type,
    updateDisabled: [...document.querySelectorAll("button")].find(button => button.textContent.trim() === "Update").disabled
  })`);
}

export default async function action() {
  await command("wait", "1000");
  await command("fill", "input[name='newPassword']", "abc");
  await command("click", "input[name='newPassword'] + div button");
  await observe("old-empty/new-invalid", "", "abc");

  await command("fill", "input[name='oldPassword']", "CurrentPass123!");
  await observe("old-filled/new-invalid", "CurrentPass123!", "abc");

  await command("fill", "input[name='oldPassword']", "");
  await command("fill", "input[name='newPassword']", "NextPass123!");
  await observe("old-empty/new-valid", "", "NextPass123!");

  await command("fill", "input[name='oldPassword']", "CurrentPass123!");
  await observe("old-filled/new-valid", "CurrentPass123!", "NextPass123!");
}
