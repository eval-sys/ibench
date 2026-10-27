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
  await agentBrowser("open", "http://localhost:3000/")
  await agentBrowser("storage", "local", "clear")
  await agentBrowser("storage", "session", "clear")
  await agentBrowser("cookies", "clear")
}
