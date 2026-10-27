export default async function cleanup() {
  // Public browsing creates no browser-owned persistent fixture data.
  // The trusted driver supplies a fresh browser context for each run.
}
