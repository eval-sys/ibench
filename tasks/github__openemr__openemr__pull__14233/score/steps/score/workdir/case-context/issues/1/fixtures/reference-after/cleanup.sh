#!/usr/bin/env bash
set -euo pipefail
# Restore only the configuration owned by this fixture.
php <<'PHP'
<?php
$backup = '/tmp/reproduction-14233-idle-timeout.json';
if (!file_exists($backup)) { exit; }
require '/workspace/app/sites/default/sqlconf.php';
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
$db = new mysqli($host, $login, $pass, $dbase, (int)$port);
$original = json_decode(file_get_contents($backup), true, flags: JSON_THROW_ON_ERROR);
$db->begin_transaction();
$rows = $db->query("SELECT gl_name,gl_index,gl_value FROM globals WHERE gl_name='timeout' ORDER BY gl_index")->fetch_all(MYSQLI_ASSOC);
if ($rows !== $original && (count($rows) !== 1 || $rows[0]['gl_value'] !== '5')) {
    throw new RuntimeException('Refusing to replace an idle timeout changed outside the fixture');
}
$db->query("DELETE FROM globals WHERE gl_name='timeout'");
$insert = $db->prepare('INSERT INTO globals(gl_name,gl_index,gl_value) VALUES (?,?,?)');
foreach ($original as $row) {
    $insert->bind_param('sis', $row['gl_name'], $row['gl_index'], $row['gl_value']);
    $insert->execute();
}
$db->commit();
unlink($backup);
echo "Original idle timeout restored.\n";
PHP
