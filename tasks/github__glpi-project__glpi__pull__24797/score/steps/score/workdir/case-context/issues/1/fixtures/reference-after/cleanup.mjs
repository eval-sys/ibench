import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

export default async function cleanup() {
  // No changes are saved in the editor. Clear authentication and menu cookies;
  // the trusted driver discards the browser session, including unsaved edits.
  await promisify(execFile)('agent-browser', ['cookies', 'clear']);
}
