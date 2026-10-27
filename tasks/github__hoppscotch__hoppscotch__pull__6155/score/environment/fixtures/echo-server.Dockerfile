FROM node:22.23.2-alpine@sha256:b6f26b36c8ff49624cfdac716b8ea1138d606df02586a77d364bb5536a634f85

COPY --chown=node:node fixtures/echo-server.mjs /app/echo-server.mjs

USER node
EXPOSE 8080
CMD ["node", "/app/echo-server.mjs"]
