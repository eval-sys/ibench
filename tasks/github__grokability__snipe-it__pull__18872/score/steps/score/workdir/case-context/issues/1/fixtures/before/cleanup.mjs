export default async function cleanup() {
  // No fixture-owned browser storage persists outside the session.
  // The trusted driver resets the browser before setup and after capture.
}
