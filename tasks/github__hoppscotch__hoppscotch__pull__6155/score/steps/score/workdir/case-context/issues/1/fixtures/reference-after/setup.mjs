import { execFile } from "node:child_process"
import { promisify } from "node:util"

const execFileAsync = promisify(execFile)

const agentBrowser = (...args) =>
  execFileAsync("agent-browser", args, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  })

const visibleAddNew =
  'xpath=//button[normalize-space(.)="Add new" and not(ancestor::*[contains(translate(@style, " ", ""), "display:none")])]'

export default async function setup() {
  // APP_URL points to the admin service; the captured REST witness uses port 3000.
  const requestPage = new URL(process.env.APP_URL)
  requestPage.port = "3000"
  requestPage.pathname = "/"
  requestPage.search = ""
  requestPage.hash = ""
  await agentBrowser("open", requestPage.href)
  await agentBrowser(
    "wait",
    '[contenteditable="true"][aria-label="Enter a URL or paste a cURL command"]'
  )

  await agentBrowser("click", 'button[aria-label="Environments"]')
  await agentBrowser("wait", "--text", "Environments are empty")
  await agentBrowser("click", visibleAddNew)
  await agentBrowser("wait", "--text", "New Environment")

  await agentBrowser("find", "label", "Label", "fill", "Website Variables")
  await agentBrowser(
    "click",
    'xpath=//*[@role="dialog"]//button[normalize-space(.)="Add new"]'
  )
  await agentBrowser("wait", '[role="dialog"] input[name="variable0"]')
  await agentBrowser(
    "fill",
    '[role="dialog"] input[name="variable0"]',
    "site"
  )
  await agentBrowser(
    "fill",
    '[role="dialog"] [contenteditable="true"][aria-label="Initial value 1"]',
    "example"
  )
  await agentBrowser(
    "fill",
    '[role="dialog"] [contenteditable="true"][aria-label="Current value 1"]',
    "example"
  )
  await agentBrowser(
    "click",
    'xpath=//*[@role="dialog"]//button[normalize-space(.)="Save"]'
  )
  await agentBrowser(
    "wait",
    "--fn",
    '!document.querySelector(\'[role="dialog"]\')'
  )

  const requestURL =
    '[contenteditable="true"][aria-label="Enter a URL or paste a cURL command"]'
  await agentBrowser("click", requestURL)
  await agentBrowser("press", "Control+a")
  await agentBrowser("keyboard", "type", "https://<<site>>.com")
  await agentBrowser("wait", ".env-highlight")
  await agentBrowser(
    "wait",
    "--fn",
    '!document.body.innerText.includes("Environment created")'
  )
}
