export default async function cleanup() {
  // There is no browser-owned fixture state. The trusted driver resets the session;
  // cleanup.sh removes the issue-owned survey and its related server state.
}
