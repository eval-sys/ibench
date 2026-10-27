import { execFile } from "node:child_process"
import { promisify } from "node:util"

const execFileAsync = promisify(execFile)

const agentBrowser = (...args) =>
  execFileAsync("agent-browser", args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  })

export default async function cleanup() {
  // APP_URL points to the admin service; the captured REST witness uses port 3000.
  const requestPage = new URL(process.env.APP_URL)
  requestPage.port = "3000"
  requestPage.pathname = "/"
  requestPage.search = ""
  requestPage.hash = ""
  await agentBrowser("open", requestPage.href)
  await agentBrowser("storage", "local", "clear")
  await agentBrowser("storage", "session", "clear")
  await agentBrowser("cookies", "clear")
}
