import config from './vite.config'

// Older baselines bundle EJS's mixed ESM/CJS entry through vite-node incorrectly.
// Keep its native module loading, as well as macOS-only fsevents, outside Vite.
// Peer dependency variants must share the framework's decorator/context registry.
export default {
  ...config,
  resolve: { ...config.resolve, dedupe: ['@tsuki-hono/common'] },
  ssr: { ...config.ssr, noExternal: /^(?!.*\/(?:ejs|fsevents)\/)/ },
}
