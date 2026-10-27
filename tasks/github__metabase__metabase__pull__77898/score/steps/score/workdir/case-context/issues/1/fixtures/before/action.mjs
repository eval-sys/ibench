import { execFile } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const evidence = new URL("../evidence/", import.meta.url).pathname;
const inviteeEmail = "invite-marketing-77898@example.test";

async function browser(...args) {
  const result = await execFileAsync("agent-browser", args, {
    timeout: 60_000,
  });
  if (result.stdout) process.stdout.write(result.stdout);
  return result;
}

export default async function action() {
  await mkdir(evidence, { recursive: true });
  // Step 1: present the collection's access split before opening the invite flow.
  await browser("find", "role", "cell", "hover", "--name", "Sales", "--exact");
  await browser("snapshot", "-s", "[role=dialog]");
  await browser("wait", "1000");

  // Step 2: close the permissions view and open its dashboard.
  await browser("find", "role", "button", "click", "--name", "Cancel", "--exact");
  await browser("wait", "--text", "Campaign Performance");
  await browser("wait", "600");
  await browser(
    "click",
    'a[href="/dashboard/7789801-campaign-performance"]',
  );
  await browser("wait", "--text", "This dashboard is empty");
  await browser("wait", "600");

  // Step 3: open the dashboard's user-facing invite flow.
  await browser("find", "role", "button", "click", "--name", "Share", "--exact");
  await browser("wait", "500");
  await browser(
    "find",
    "role",
    "menuitem",
    "click",
    "--name",
    "Invite someone to view this",
    "--exact",
  );
  await browser("wait", "--text", "Invite someone to view this dashboard");
  await browser("wait", "500");

  // Complete the required invitation field so its action state can be observed.
  await browser("find", "role", "textbox", "fill", "--name", "Email", "--exact", inviteeEmail);

  // Step 4: open the picker and select one no-access and one access group.
  await browser("wait", '[role="combobox"][aria-label="Groups"]');
  await browser("find", "role", "combobox", "click", "--name", "Groups", "--exact");
  await browser("snapshot");
  await browser("screenshot", `${evidence}/groups.png`);
  await browser("wait", "1000");
  await browser("find", "role", "option", "click", "--name", "Marketing", "--exact");
  // Close the dropdown to expose the inline guidance below the field.
  await browser("press", "Escape");
  await browser("wait", "1500");
  await browser("snapshot");
  await browser("screenshot", `${evidence}/marketing-warning.png`);
  await browser("is", "enabled", "button[type=submit]");
  await browser("find", "role", "combobox", "click", "--name", "Groups", "--exact");
  await browser("find", "role", "option", "click", "--name", "Sales", "--exact");
  await browser("press", "Escape");
  await browser("wait", "600");
  await browser("snapshot");
  await browser("screenshot", `${evidence}/marketing-sales.png`);

  // Send while none of the selected memberships grants dashboard access.
  await browser("find", "role", "combobox", "click", "--name", "Groups", "--exact");
  await browser("find", "role", "option", "click", "--name", "Sales", "--exact");
  await browser("press", "Escape");
  await browser("wait", "600");
  await browser("snapshot");
  await browser("screenshot", `${evidence}/send-without-access.png`);
  await browser("find", "role", "button", "click", "--name", "Send invitation", "--exact");
  await browser("wait", "--text", "Invitation sent");
  await browser("snapshot");
  await browser("screenshot", `${evidence}/invitation-sent.png`);

  // Read persisted state after the UI submission; never create users by API.
  const result = await browser("eval", `(async () => {
    const read = async (url) => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(url + ': ' + response.status);
      return response.json();
    };
    const users = await read('/api/user');
    const invitee = users.data.find(user => user.email === '${inviteeEmail}');
    if (!invitee) return { email: '${inviteeEmail}', user: null };
    const user = await read('/api/user/' + invitee.id);
    const groups = await read('/api/permissions/group');
    return {
      requests: ['/api/user', '/api/user/' + invitee.id, '/api/permissions/group'],
      email: user.email,
      user_id: user.id,
      is_active: user.is_active,
      is_superuser: user.is_superuser,
      memberships: user.user_group_memberships.map(membership => ({
        id: membership.id,
        name: groups.find(group => group.id === membership.id)?.name,
        is_group_manager: membership.is_group_manager,
      })),
    };
  })()`);
  await writeFile(`${evidence}/invitation-result.json`, result.stdout);
}
