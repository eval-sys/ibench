export default async function cleanup() {
  // No browser-owned fixture state. The trusted driver isolates authentication
  // in a clean browser session and disposes of that session after the replay.
}
