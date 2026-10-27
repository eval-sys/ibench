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

export default async function action() {
  // Leave a readable opening frame before changing the cover.
  await command("wait", 'button[type="submit"]');
  await command("wait", "--fn", "Boolean(document.querySelector('img[alt=\"Avery\"]')?.complete && document.querySelector('img[alt=\"Avery\"]')?.naturalWidth)");
  await command("wait", "1000");
  console.log("Initial profile cover:");
  await command("get", "attr", 'img[alt="Avery"]', "src");
  await command("find", "role", "button", "click", "--name", "Change cover", "--exact");
  await command("wait", 'img[alt="Cover image 3"]');
  await command("wait", "500");
  await command("click", 'img[alt="Cover image 3"]');
  await command("wait", "1000");
  console.log("Profile cover after selecting Cover image 3:");
  await command("get", "attr", 'img[alt="Avery"]', "src");

  await command("find", "role", "button", "click", "--name", "Save changes", "--exact");
  await command("wait", "1500");
  console.log("Profile cover and actual feedback after Save changes:");
  await command("get", "attr", 'img[alt="Avery"]', "src");
  await command("snapshot", "-i");

  await command("click", '[role="dialog"] button:has(svg.lucide-x)');
  await command("wait", "--fn", "document.querySelector('[role=dialog]') === null");

  await command("click", userMenuButton);
  await command("find", "role", "menuitem", "click", "--name", "Settings", "--exact");
  await command("wait", 'button[type="submit"]');
  await command(
    "wait",
    "--fn",
    "Boolean(document.querySelector('img[alt=\"Avery\"]')?.complete && document.querySelector('img[alt=\"Avery\"]')?.naturalWidth)"
  );
  console.log("Profile cover after closing and reopening Settings:");
  await command("get", "attr", 'img[alt="Avery"]', "src");
}
