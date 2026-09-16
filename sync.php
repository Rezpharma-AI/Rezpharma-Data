<?php
// sync.php — replicates the Railway master DB onto this host
// CLI cron:   php /home/rezphng/domains/rezpharmacdss.me/public_html/sync.php
// Web cron:   https://rezpharmacdss.me/sync.php?key=WEBKEY_CHANGE_ME
set_time_limit(120); ignore_user_abort(true);

$API   = 'https://rezpharmaai-production.up.railway.app';
$TOKEN = 'rzp_sync_9498ad2749884198a9da82e66aec24b1822e010cba1240f9b70af8575115b04e';      // must equal SYNC_TOKEN on Railway
$WEBKEY= 'CHANGE_ME_WEB_KEY';          // only used for web-cron mode
$DIR   = __DIR__ . '/kb';
$CHUNK = 50 * 1024 * 1024;              // 50 MB per range request
$BUDGET= 25;                           // seconds of downloading per run

if (php_sapi_name() !== 'cli' && ($_GET['key'] ?? '') !== $WEBKEY) { http_response_code(403); exit('forbidden'); }
@mkdir($DIR);
$stateFile = "$DIR/sync_state.json";
$partFile  = "$DIR/rezpharma.db.part";
$liveFile  = "$DIR/rezpharma_live.db";
$state = is_file($stateFile) ? json_decode(file_get_contents($stateFile), true) : [];

function api_meta($url, $token) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>30,
        CURLOPT_HTTPHEADER=>["X-Sync-Token: $token"]]);
    $raw = curl_exec($ch); $code = curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    return [$code, json_decode($raw, true)];
}

list($code, $meta) = api_meta("$API/api/v1/export/checksum", $TOKEN);
if ($code !== 200 || !$meta) exit("meta failed ($code)\n");
if (($state['sha256'] ?? '') === $meta['sha256'] && is_file($liveFile)) exit("up-to-date\n");

$offset = is_file($partFile) ? filesize($partFile) : 0;
if (($state['target_sha'] ?? '') !== $meta['sha256']) { @unlink($partFile); $offset = 0; }
$state['target_sha'] = $meta['sha256'];

$start = time();
$fp = fopen($partFile, 'ab');
while (true) {
    if (time() - $start > $BUDGET) break;
    $end = min($offset + $CHUNK, $meta['size']) - 1;
    $ch = curl_init("$API/api/v1/export/snapshot");
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>true, CURLOPT_TIMEOUT=>60,
        CURLOPT_HTTPHEADER=>["X-Sync-Token: $TOKEN", "Range: bytes=$offset-$end"]]);
    $data = curl_exec($ch); $code = curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if ($data === false || !in_array($code, [200, 206]) || strlen($data) === 0) break;
    fwrite($fp, $data); $offset += strlen($data);
    if ($offset >= $meta['size']) break;
}
fclose($fp);

if ($offset >= $meta['size']) {
    if (hash_file('sha256', $partFile) === $meta['sha256']) {
        rename($partFile, $liveFile);                 // atomic swap
        $state['sha256'] = $meta['sha256']; $state['synced_at'] = date('c');
        echo "synced {$meta['sha256']}\n";
    } else { @unlink($partFile); echo "checksum mismatch, discarded\n"; }
} else {
    echo 'progress: ' . round($offset / max(1, $meta['size']) * 100, 1) . "%\n";
}
$state['offset'] = $offset;
file_put_contents($stateFile, json_encode($state));