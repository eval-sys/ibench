import { createServer } from "node:http"

const port = Number(process.env.PORT ?? 8080)
const maxBodyBytes = 1024 * 1024
const maxDelayMs = 5000

const corsHeaders = (request) => ({
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD",
  "access-control-allow-headers":
    request.headers["access-control-request-headers"] ??
    "Origin, X-Requested-With, Content-Type, Accept, Authorization",
  "access-control-max-age": "600",
})

const queryArgs = (url) => {
  const args = {}
  for (const key of new Set(url.searchParams.keys())) {
    args[key] = url.searchParams.getAll(key).join(", ")
  }
  return args
}

const echoPayload = (request, url, body) => {
  const data = body.toString("utf8")
  const isBase64Encoded = !Buffer.from(data, "utf8").equals(body)

  return {
    method: request.method,
    args: queryArgs(url),
    data: isBase64Encoded ? body.toString("base64") : data,
    headers: request.headers,
    path: url.pathname,
    isBase64Encoded,
  }
}

const sendJson = (request, response, status, payload) => {
  const body = JSON.stringify(payload, null, 2) + "\n"
  response.writeHead(status, {
    ...corsHeaders(request),
    "cache-control": "no-store",
    "content-type": "application/json; charset=utf-8",
  })
  response.end(request.method === "HEAD" || status === 204 || status === 304 ? undefined : body)
}

createServer((request, response) => {
  const url = new URL(request.url, `http://${request.headers.host ?? "echo"}`)

  if (url.pathname === "/healthz") {
    response.writeHead(200, { "content-type": "text/plain; charset=utf-8" })
    response.end("ok\n")
    return
  }

  const chunks = []
  let size = 0
  request.on("data", (chunk) => {
    size += chunk.length
    if (size <= maxBodyBytes) chunks.push(chunk)
  })
  request.on("end", () => {
    if (size > maxBodyBytes) {
      sendJson(request, response, 413, { error: "request body exceeds 1 MiB" })
      return
    }

    const body = Buffer.concat(chunks)
    const statusMatch = url.pathname.match(/^\/__fixture\/status\/(\d{3})$/)
    const delayMatch = url.pathname.match(/^\/__fixture\/delay\/(\d+)$/)

    if (statusMatch) {
      const status = Number(statusMatch[1])
      if (status < 200 || status > 599) {
        sendJson(request, response, 400, { error: "status must be between 200 and 599" })
        return
      }
      sendJson(request, response, status, echoPayload(request, url, body))
      return
    }

    if (delayMatch) {
      const delay = Number(delayMatch[1])
      if (delay > maxDelayMs) {
        sendJson(request, response, 400, { error: `delay must not exceed ${maxDelayMs}ms` })
        return
      }
      setTimeout(() => sendJson(request, response, 200, echoPayload(request, url, body)), delay)
      return
    }

    if (url.pathname.startsWith("/__fixture/")) {
      sendJson(request, response, 404, { error: "unknown fixture route" })
      return
    }

    sendJson(request, response, 200, echoPayload(request, url, body))
  })
}).listen(port, "0.0.0.0", () => {
  console.log(`Hoppscotch echo fixture listening on ${port}`)
})
