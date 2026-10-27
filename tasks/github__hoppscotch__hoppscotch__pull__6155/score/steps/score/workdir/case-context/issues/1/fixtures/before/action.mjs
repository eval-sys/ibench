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

  const variable = await getBox(".env-highlight")
  const tooltip = await getBox(".cm-tooltip .tippy-box")
  const editButton = await getBox(".cm-tooltip .tippy-box button")

  await agentBrowser("wait", "500")

  const gapX = Math.round(variable.x + variable.width + 10)
  const gapY = Math.round(tooltip.y - 3)
  await agentBrowser("mouse", "move", String(gapX), String(gapY))

  const editX = Math.round(editButton.x + editButton.width / 2)
  const editY = Math.round(editButton.y + editButton.height / 2)
  await agentBrowser("mouse", "move", String(editX), String(editY))
}
