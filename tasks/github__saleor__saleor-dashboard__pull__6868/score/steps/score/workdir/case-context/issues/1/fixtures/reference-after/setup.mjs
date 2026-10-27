import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const command = async (...arguments_) => {
  const result = await execFileAsync("agent-browser", arguments_, {
    timeout: 120_000,
    maxBuffer: 1024 * 1024,
  });

  return result.stdout;
};

const waitForFixtureRow = async () => {
  await command("wait", ".dvn-scroller");

  for (let attempt = 0; attempt < 40; attempt += 1) {
    const snapshot = await command("snapshot", "-i");

    if (snapshot.includes('gridcell "Aurora Desk Lamp"')) {
      return;
    }

    await command("wait", "250");
  }

  throw new Error("Aurora Desk Lamp did not appear in the product catalogue");
};

export default async function setup() {
  await command("open", process.env.APP_URL || "http://localhost:9000/");
  await command("wait", "[data-test-id='email']");
  await command("find", "label", "Email address", "fill", "catalogue.manager.6868@example.com");
  await command("find", "label", "Password", "fill", "CatalogueRow!6868");
  await command("find", "role", "button", "click", "--name", "Sign in");
  await command("wait", "--url", "**/home");
  await command("wait", "a[href='/products/']");
  await command("click", "a[href='/products/']");
  await command("wait", "--url", "**/products/**");
  await waitForFixtureRow();

  await command(
    "find",
    "role",
    "button",
    "click",
    "--name",
    "Dismiss Pulse announcement",
  ).catch(() => undefined);
  await waitForFixtureRow();
}
