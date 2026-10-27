import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const arguments_ = process.argv.slice(2);
const requireAll = arguments_.includes('--require-all');
const positional = arguments_.filter(argument => argument !== '--require-all');
const inputRoot = positional[0];
if (!inputRoot) throw new Error('usage: node run-replay.mjs <input-root> [output-root] [--require-all]');
const config = JSON.parse(fs.readFileSync(path.join(inputRoot, 'input.json'), 'utf8'));
const outputRoot = positional[1] || path.join('/logs/artifacts/solver', config.task);
const databaseURL = process.env.DATABASE_URL || '';
const trustedReplay = path.join(inputRoot, 'replay.mjs');
fs.mkdirSync(outputRoot, { recursive: true });

const run = (command, arguments_, options = {}) => {
  const result = spawnSync(command, arguments_, {
    encoding: 'utf8',
    env: options.env ?? process.env,
    timeout: options.timeout ?? 300_000,
  });
  return {
    code: result.status ?? 1,
    error: result.error ? String(result.error) : '',
    stderr: result.stderr || '',
    stdout: result.stdout || '',
  };
};
const write = (file, value) => fs.writeFileSync(file, value, 'utf8');
const browserVersion = run('agent-browser', ['--version']).stdout.trim() || 'unavailable';
const cases = [];

for (const item of config.issues) {
  const fixture = path.join(inputRoot, 'issues', item.directory);
  const output = path.join(outputRoot, item.directory);
  const replayResultPath = path.join(output, 'replay-result.json');
  fs.mkdirSync(output, { recursive: true });

  const browserSession = `evidence-${createHash('sha256').update(item.issue_id).digest('hex').slice(0, 16)}`;
  let viewport = item.viewport || config.default_viewport;
  const env = {
    ...process.env,
    AGENT_BROWSER_NAMESPACE: browserSession,
    AGENT_BROWSER_SESSION: browserSession,
    REPLAY_VIEWPORT: viewport,
  };
  let status = 'fixture_invalid';
  let failure = null;
  let replay = { stdout: '', stderr: '' };
  let setup = { stdout: '', stderr: '' };
  let cleanup = { stdout: '', stderr: '' };
  let capture = { stdout: '', stderr: '' };
  let runServerFixture = null;
  let fixtureMode = null;
  const captureManifest = {
    schema_version: 'evidence-replay-capture/v1',
    entry_path: item.entry_path || null,
    record_url: null,
    record_started_at_ms: null,
    record_stopped_at_ms: null,
    record_elapsed_ms: null,
    video_duration_ms: null,
    ffprobe: null,
  };

  try {
    const presentation = JSON.parse(fs.readFileSync(path.join(fixture, 'presentation.json'), 'utf8'));
    viewport = item.viewport || presentation.viewport || config.default_viewport;
    env.REPLAY_VIEWPORT = viewport;
    const entryPath = item.entry_path || presentation.entry_path || null;
    captureManifest.entry_path = entryPath;
    fixtureMode = presentation.fixture_mode || 'database-and-browser';
    if (!['database-and-browser', 'script-and-browser', 'browser-only'].includes(fixtureMode)) {
      throw new Error(`unsupported fixture_mode: ${fixtureMode}`);
    }
    if (fixtureMode === 'database-and-browser') {
      runServerFixture = phase => run(
        'psql',
        ['-d', databaseURL, '-v', 'ON_ERROR_STOP=1', '-f', path.join(fixture, `${phase}.sql`)],
        { env },
      );
    } else if (fixtureMode === 'script-and-browser') {
      runServerFixture = phase => run('bash', [path.join(fixture, `${phase}.sh`)], { env });
    }
    if (runServerFixture) {
      cleanup = runServerFixture('cleanup');
      if (cleanup.code !== 0) failure = `cleanup.${fixtureMode === 'database-and-browser' ? 'sql' : 'sh'} failed`;
    }
    if (!failure && runServerFixture) {
      setup = runServerFixture('setup');
      if (setup.code !== 0) failure = `setup.${fixtureMode === 'database-and-browser' ? 'sql' : 'sh'} failed`;
    }
    if (!failure && !entryPath) {
      failure = 'presentation.json entry_path is missing';
    }
    if (!failure) {
      const result = run('node', [trustedReplay, fixture, output], { env, timeout: 600_000 });
      replay = { stdout: result.stdout, stderr: result.stderr + result.error };
      const replayResult = fs.existsSync(replayResultPath)
        ? JSON.parse(fs.readFileSync(replayResultPath, 'utf8'))
        : {};
      fs.rmSync(replayResultPath, { force: true });
      captureManifest.record_url = replayResult.record_url ?? null;
      captureManifest.capture_method = replayResult.capture_method ?? null;
      captureManifest.frame_size = replayResult.frame_size ?? null;
      captureManifest.record_started_at_ms = replayResult.record_started_at_ms ?? null;
      captureManifest.record_stopped_at_ms = replayResult.record_stopped_at_ms ?? null;
      captureManifest.record_elapsed_ms = replayResult.record_elapsed_ms ?? null;
      captureManifest.video_duration_ms = replayResult.video_duration_ms ?? null;
      captureManifest.ffprobe = replayResult.ffprobe ?? null;
      capture.stdout = replayResult.ffprobe?.stdout || '';
      capture.stderr = replayResult.ffprobe?.stderr || '';

      const failurePhase = replayResult.failure_phase;
      failure = replayResult.failure_summary || null;
      if (['load', 'cleanup', 'setup'].includes(failurePhase)) status = 'fixture_invalid';
      else if (['record', 'screenshot', 'stop', 'capture'].includes(failurePhase)) status = 'capture_failed';
      else if (result.code !== 0) status = 'replay_failed';
      else {
        status = 'replay_passed';
        failure = null;
      }
    }
  } catch (error) {
    failure = String(error);
  } finally {
    if (runServerFixture) {
      const finalCleanup = runServerFixture('cleanup');
      cleanup.stdout += finalCleanup.stdout;
      cleanup.stderr += finalCleanup.stderr;
      if (finalCleanup.code !== 0 && status === 'replay_passed') {
        status = 'fixture_invalid';
        failure = `final cleanup.${fixtureMode === 'database-and-browser' ? 'sql' : 'sh'} failed`;
      }
    }
  }

  write(path.join(output, 'setup.log'), setup.stdout + setup.stderr);
  write(path.join(output, 'cleanup.log'), cleanup.stdout + cleanup.stderr);
  write(path.join(output, 'capture.log'), capture.stdout + capture.stderr);
  write(path.join(output, 'replay.stdout.log'), replay.stdout);
  write(path.join(output, 'replay.stderr.log'), replay.stderr);
  cases.push({
    capture: captureManifest,
    directory: item.directory,
    issue_id: item.issue_id,
    viewport,
    failure_summary: failure,
    status,
  });
}

write(
  path.join(outputRoot, 'manifest.json'),
  JSON.stringify(
    {
      browser_version: browserVersion,
      cases,
      commit_id: config.commit_id,
      pull_request_number: config.pull_request_number,
      repository: config.repository,
      schema_version: 'evidence-replay-driver/v3',
      task: config.task,
    },
    null,
    2,
  ),
);

if (requireAll) {
  const failed = cases.filter(item => item.status !== 'replay_passed');
  for (const item of failed) {
    console.error(`${item.issue_id}: ${item.status}: ${item.failure_summary || 'replay did not pass'}`);
  }
  if (failed.length) process.exitCode = 1;
}
