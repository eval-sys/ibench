import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const command = async (...args) => {
  const { stdout, stderr } = await execFileAsync("agent-browser", args, {
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  if (stdout) process.stdout.write(stdout);
  if (stderr) process.stderr.write(stderr);
};

const userMenuButton =
  'div[data-main-menu="true"] > button:has(div[style*="height: 20px"][style*="width: 20px"])';

export default async function setup() {
  await command("open", new URL("/", process.env.APP_URL).href);
  await command("wait", 'input[type="email"]');
  await command("fill", 'input[type="email"]', "avery.morgan@example.com");
  await command("find", "role", "button", "click", "--name", "Continue", "--exact");
  await command("wait", 'input[type="password"]');
  await command("fill", 'input[type="password"]', "Canvas-Profile-2026!");
  await command("find", "role", "button", "click", "--name", "Go to workspace", "--exact");
  await command("wait", "--url", "**/creative-studio/");
  await command("wait", "--text", "Creative Studio");
  await command("click", userMenuButton);
  await command("find", "role", "menuitem", "click", "--name", "Settings", "--exact");
  await command("wait", 'button[type="submit"]');
  await command("wait", 'img[alt="Avery"][src*="image_1-"]');
  await command("wait", "--fn", "Boolean(document.querySelector('img[alt=\"Avery\"]')?.complete && document.querySelector('img[alt=\"Avery\"]')?.naturalWidth)");
  console.log("Initial profile cover:");
  await command("get", "attr", 'img[alt="Avery"]', "src");
}
