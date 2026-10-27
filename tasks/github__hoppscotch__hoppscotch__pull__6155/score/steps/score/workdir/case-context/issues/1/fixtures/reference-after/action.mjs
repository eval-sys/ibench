import { execFile } from "node:child_process"
import { promisify } from "node:util"

const execFileAsync = promisify(execFile)

const agentBrowser = (...args) =>
  execFileAsync("agent-browser", args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  })

const getBox = async (selector) => {
  const { stdout } = await agentBrowser("get", "box", selector, "--json")
  const result = JSON.parse(stdout)
  if (!result.success) throw new Error(`Unable to measure ${selector}`)
  return result.data
}

export default async function action() {
  await agentBrowser("hover", ".env-highlight")
  await agentBrowser("wait", ".cm-tooltip .tippy-box button")

  // CodeMirror initially attaches the tooltip offscreen before positioning it.
  await agentBrowser("wait", "--fn",
    '(() => { const r = document.querySelector(".cm-tooltip .tippy-box")?.getBoundingClientRect(); return r && r.top >= 0 && r.bottom <= innerHeight; })()')
  await agentBrowser("wait", "500")
  const variable = await getBox(".env-highlight")
  const tooltip = await getBox(".cm-tooltip .tippy-box")

  const { stdout: tooltipText } = await agentBrowser("get", "text", ".cm-tooltip")
  if (!tooltipText.includes("Website Variables") || !tooltipText.includes("example")) {
    throw new Error("The site tooltip does not show its Website Variables value")
  }
  await agentBrowser("wait", "500")

  const gapX = Math.round(variable.x + variable.width + 10)
  const gapY = Math.round(tooltip.y - 3)
  // Move through the space between the URL token and tooltip, not straight
  // to the edit button. These built-in pointer commands preserve hover handling.
  const startX = variable.x + variable.width / 2
  const startY = variable.y + variable.height / 2
  for (let step = 1; step <= 4; step++) {
    await agentBrowser("mouse", "move",
      String(Math.round(startX + (gapX - startX) * step / 4)),
      String(Math.round(startY + (gapY - startY) * step / 4)))
  }
  await agentBrowser("wait", "150")
  const { stdout: inGap } = await agentBrowser("is", "visible", ".cm-tooltip .tippy-box button", "--json")
  if (!JSON.parse(inGap).data?.visible) throw new Error("The edit control disappeared during the approach")

  await agentBrowser("hover", ".cm-tooltip .tippy-box button")
  await agentBrowser("wait", "500")
  await agentBrowser("click", ".cm-tooltip .tippy-box button")
  await agentBrowser("wait", "[role=\"dialog\"]")
  await agentBrowser("wait", "--text", "Edit Environment")
  const { stdout: label } = await agentBrowser("get", "value", '[role="dialog"] input[required]')
  const { stdout: variableName } = await agentBrowser("get", "value", '[role="dialog"] input[name="variable0"]')
  const { stdout: initial } = await agentBrowser("get", "text", '[role="dialog"] [contenteditable="true"][aria-label="Initial value 1"]')
  const { stdout: current } = await agentBrowser("get", "text", '[role="dialog"] [contenteditable="true"][aria-label="Current value 1"]')
  if (label.trim() !== "Website Variables" || variableName.trim() !== "site" || initial.trim() !== "example" || current.trim() !== "example") {
    throw new Error("Edit did not open the site variable in Website Variables")
  }
}
