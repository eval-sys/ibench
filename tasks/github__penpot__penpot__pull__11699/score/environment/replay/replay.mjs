import { execFile } from 'node:child_process';
import { mkdir, realpath, rm, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);
const [fixtureArgument, outputArgument] = process.argv.slice(2);

if (!fixtureArgument || !outputArgument) {
  throw new Error('usage: node replay.mjs <fixture-directory> <output-directory>');
}

const fixtureDirectory = await realpath(fixtureArgument);
const outputDirectory = path.resolve(outputArgument);
process.env.REPLAY_OUTPUT_DIRECTORY = outputDirectory;
const resultPath = path.join(outputDirectory, 'replay-result.json');
const videoPath = path.join(outputDirectory, 'replay.webm');
const screenshotPath = path.join(outputDirectory, 'final.png');
const actionPaddingMs = 2000;
await mkdir(outputDirectory, { recursive: true });
await Promise.all([resultPath, videoPath, screenshotPath].map((file) => rm(file, { force: true })));

const command = async (...arguments_) => {
  const result = await execFileAsync('agent-browser', arguments_, {
    env: process.env,
    maxBuffer: 1024 * 1024,
    timeout: 120_000,
  });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  return result;
};

const closeBrowser = async () => {
  await command('close');
  // agent-browser 0.33 returns before its daemon exits. Reusing it during
  // shutdown can lose the socket before the next command's launch request.
  const deadline = Date.now() + 10_000;
  while (true) {
    const { stdout } = await execFileAsync('agent-browser', ['session', 'info', '--json'], {
      env: process.env,
      timeout: 1000,
    });
    const status = JSON.parse(stdout);
    if (!status.success || typeof status.data?.active !== 'boolean') {
      throw new Error('Invalid agent-browser session status after close');
    }
    if (!status.data.active) return;
    const remaining = deadline - Date.now();
    if (remaining <= 0) {
      throw new Error('agent-browser session is still active 10 seconds after close');
    }
    await new Promise((resolve) => setTimeout(resolve, Math.min(200, remaining)));
  }
};

const setViewport = async () => {
  const [width, height] = process.env.REPLAY_VIEWPORT.split('x');
  await command('set', 'viewport', width, height);
};

let failure;
let phase = 'load';
let recordStarted = false;
let recordURL = null;
let recordStartedAt = null;
let recordStoppedAt = null;
let videoDurationMs = null;

try {
  const setupModule = await import(pathToFileURL(path.join(fixtureDirectory, 'setup.mjs')));
  const cleanupModule = await import(pathToFileURL(path.join(fixtureDirectory, 'cleanup.mjs')));
  const actionModule = await import(pathToFileURL(path.join(fixtureDirectory, 'action.mjs')));
  if (
    typeof cleanupModule.default !== 'function' ||
    typeof setupModule.default !== 'function' ||
    typeof actionModule.default !== 'function'
  ) {
    throw new TypeError('cleanup.mjs, setup.mjs, and action.mjs must each export one default function');
  }

  await closeBrowser();
  await setViewport();

  phase = 'cleanup';
  await cleanupModule.default();

  await closeBrowser();
  await setViewport();

  phase = 'setup';
  await setupModule.default();
  recordURL = (await command('get', 'url')).stdout.trim() || null;

  phase = 'record';
  recordStartedAt = Date.now();
  await command('record', 'restart', videoPath, '--fps', '10');
  recordStarted = true;

  phase = 'action';
  await actionModule.default();
  await command('wait', String(actionPaddingMs));

  phase = 'screenshot';
  await command('screenshot', screenshotPath);
} catch (error) {
  failure = error;
} finally {
  if (recordStarted) {
    try {
      phase = failure ? phase : 'stop';
      await command('record', 'stop');
      recordStoppedAt = Date.now();
    } catch (error) {
      if (!failure) failure = error;
      phase = 'stop';
    }
  }
  try {
    const cleanupModule = await import(pathToFileURL(path.join(fixtureDirectory, 'cleanup.mjs')));
    await cleanupModule.default();
  } catch (error) {
    if (!failure) {
      failure = error;
      phase = 'cleanup';
    }
  }
  try {
    await closeBrowser();
  } catch (error) {
    if (!failure) {
      failure = error;
      phase = 'close';
    }
  }
  const probe = await execFileAsync(
    'ffprobe',
    ['-v', 'error', '-show_entries', 'format=duration', '-of', 'json', videoPath],
    { timeout: 30_000 },
  ).then(
    ({ stdout, stderr }) => ({ code: 0, stdout, stderr }),
    (error) => ({ code: 1, stdout: error.stdout || '', stderr: error.stderr || error.message }),
  );
  try {
    if (probe.code !== 0) throw new Error(`Video validation failed: ${probe.stderr.trim()}`);
    const duration = Number(JSON.parse(probe.stdout).format?.duration);
    if (!Number.isFinite(duration)) throw new Error('Video duration is missing or invalid');
    videoDurationMs = Math.round(duration * 1000);
    if (videoDurationMs < 500) throw new Error(`Video is too short: ${videoDurationMs}ms; at least 500ms required`);
    if (!(await stat(screenshotPath)).size) throw new Error('Final screenshot is empty');
  } catch (error) {
    if (!failure) {
      failure = error;
      phase = 'capture';
    }
  }
  await writeFile(
    resultPath,
    `${JSON.stringify(
      {
        failure_phase: failure ? phase : null,
        failure_summary: failure ? String(failure.stack || failure) : null,
        record_elapsed_ms:
          recordStartedAt && recordStoppedAt ? recordStoppedAt - recordStartedAt : null,
        record_started_at_ms: recordStartedAt,
        record_stopped_at_ms: recordStoppedAt,
        record_url: recordURL,
        video_duration_ms: videoDurationMs,
        ffprobe: probe,
      },
      null,
      2,
    )}\n`,
  );
}

if (failure) throw failure;
console.log(`Replay passed: ${videoDurationMs}ms video and final screenshot in ${outputDirectory}`);
