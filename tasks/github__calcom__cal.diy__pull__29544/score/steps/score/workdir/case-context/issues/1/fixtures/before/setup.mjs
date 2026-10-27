import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const command = async (...args) => {
  await execFileAsync("agent-browser", args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
};

export default async function setup() {
  await command("open", new URL("/auth/login", process.env.APP_URL || "http://localhost:3000").href);
  await command("wait", "input[type='email']");
  await command("find", "label", "Email", "fill", "morgan.security@example.com");
  await command("find", "label", "Password", "fill", "CurrentPass123!");
  await command("find", "role", "button", "click", "--name", "Continue", "--exact");
  await command("wait", "--url", "**/event-types");
  await command("wait", "--load", "networkidle");

  await command("find", "role", "link", "click", "--name", "Settings", "--exact");
  await command("wait", "--url", "**/settings/my-account/profile");
  await command("wait", "--load", "networkidle");
  await command("find", "role", "link", "click", "--name", "Password", "--exact");
  await command("wait", "--url", "**/settings/security/password");
  await command("wait", "input[name='newPassword']");
  await command("wait", "--fn", `(() => {
    const oldPassword = document.querySelector("input[name='oldPassword']");
    const newPassword = document.querySelector("input[name='newPassword']");
    const update = [...document.querySelectorAll("button")].find(button => button.textContent.trim() === "Update");
    return oldPassword?.value === "" && newPassword?.value === "" && update?.disabled &&
      document.body.innerText.includes("The password must be a minimum of 7 characters long containing at least one number and have a mixture of uppercase and lowercase letters");
  })()`);
}
