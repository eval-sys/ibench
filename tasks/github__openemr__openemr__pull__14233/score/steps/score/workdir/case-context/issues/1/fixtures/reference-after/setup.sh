#!/usr/bin/env bash
set -euo pipefail
# Preserve normal initialization; enable the short timeout after browser setup.
REPLAY_IDLE_TIMEOUT_PHASE="${1:-prepare}" php <<'PHP'
<?php
require '/workspace/app/sites/default/sqlconf.php';
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
$db = new mysqli($host, $login, $pass, $dbase, (int)$port);
$backup = '/tmp/reproduction-14233-idle-timeout.json';
$db->begin_transaction();
$rows = $db->query("SELECT gl_name,gl_index,gl_value FROM globals WHERE gl_name='timeout' ORDER BY gl_index")->fetch_all(MYSQLI_ASSOC);
if (file_exists($backup)) {
    $original = json_decode(file_get_contents($backup), true, flags: JSON_THROW_ON_ERROR);
    if ($rows !== $original && (count($rows) !== 1 || $rows[0]['gl_value'] !== '5')) {
        throw new RuntimeException('Refusing to overwrite a non-fixture idle timeout');
    }
} else {
    if (file_put_contents($backup, json_encode($rows, JSON_THROW_ON_ERROR)) === false) {
        throw new RuntimeException('Could not preserve the idle timeout');
    }
    chmod($backup, 0600);
}
if (getenv('REPLAY_IDLE_TIMEOUT_PHASE') === 'enable') {
    $db->query("DELETE FROM globals WHERE gl_name='timeout'");
    $db->query("INSERT INTO globals(gl_name,gl_index,gl_value) VALUES ('timeout',0,'5')");
}
$db->commit();
if (getenv('REPLAY_IDLE_TIMEOUT_PHASE') === 'enable') {
    echo json_encode($db->query("SELECT TIMESTAMPDIFF(SECOND,MAX(last_updated),NOW()) AS latest_activity_age_seconds FROM session_tracker")->fetch_assoc(), JSON_THROW_ON_ERROR) . "\n";
}
echo "Idle timeout fixture prepared; enable phase uses 5 seconds without changing polling.\n";
PHP
