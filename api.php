<?php
/**
 * RezpharmaCDSS — api.php (Scenario B: LIVE PROXY + FALLBACK)
 */
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('Access-Control-Allow-Origin: *');

$API_BASE   = 'https://rezpharmaai-production.up.railway.app';
$EP_ANALYZE = '/api/v1/m1/analyze';
$EP_ADVISOR = '/api/v1/advisor/recommendations';
$TIMEOUT    = 25;

/* --- Name Normalization (Brand -> Generic, lowercase -> Title Case) --- */
$SYNONYMS = array(
    'asa' => 'Aspirin', 'acetylsalicylic acid' => 'Aspirin',
    'coumadin' => 'Warfarin', 'jantoven' => 'Warfarin', 'marevan' => 'Warfarin',
    'tylenol' => 'Acetaminophen', 'panadol' => 'Acetaminophen', 'paracetamol' => 'Acetaminophen',
    'advil' => 'Ibuprofen', 'motrin' => 'Ibuprofen', 'brufen' => 'Ibuprofen',
    'voltaren' => 'Diclofenac', 'zocor' => 'Simvastatin', 'lipitor' => 'Atorvastatin',
    'crestor' => 'Rosuvastatin', 'cordarone' => 'Amiodarone', 'pacerone' => 'Amiodarone',
    'glucophage' => 'Metformin', 'lanoxin' => 'Digoxin', 'prilosec' => 'Omeprazole',
    'nexium' => 'Esomeprazole', 'zoloft' => 'Sertraline', 'prozac' => 'Fluoxetine',
    'paxil' => 'Paroxetine', 'cipro' => 'Ciprofloxacin',
);

$drugs = array();
if (isset($_GET['drugs'])) {
    foreach (explode(',', (string) $_GET['drugs']) as $p) {
        $key = strtolower(trim($p));
        if ($key === '') continue;
        $drugs[] = isset($SYNONYMS[$key]) ? $SYNONYMS[$key] : ucwords($key);
    }
}
$drugs = array_values(array_unique($drugs));

$mode = isset($_GET['mode']) ? $_GET['mode'] : '';

function out($payload) {
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function call_api($url, $postBody = null, $timeout = 25) {
    $ch = curl_init($url);
    curl_setopt_array($ch, array(
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT        => $timeout,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_HTTPHEADER     => array('Content-Type: application/json', 'Accept: application/json'),
    ));
    if ($postBody !== null) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($postBody));
    }
    $raw  = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);
    if ($raw === false) return array('ok' => false, 'code' => 0, 'error' => $err, 'data' => null);
    $data = json_decode($raw, true);
    $ok   = ($code >= 200 && $code < 300) && is_array($data);
    return array('ok' => $ok, 'code' => $code, 'error' => null, 'data' => $data);
}

/* --- Route: Health Ping --- */
if ($mode === 'health') {
    $r = call_api($API_BASE . '/', null, $TIMEOUT);
    out(array('engine' => $r['ok'] ? 'up' : 'down', 'http' => $r['code'], 'data' => $r['data']));
}

/* --- Route: Advisor Top-3 --- */
if ($mode === 'advisor') {
    $r = call_api($API_BASE . $EP_ADVISOR, null, $TIMEOUT);
    if (!$r['ok']) out(array('recommendations' => null, 'live' => false, 'http' => $r['code']));
    $recs = isset($r['data']['alerts_selected']) ? $r['data']['alerts_selected'] : (isset($r['data']['recommendations']) ? $r['data']['recommendations'] : $r['data']);
    out(array('recommendations' => $recs, 'live' => true, 'source' => 'railway_advisor'));
}

/* --- Route: DDI Analyze (Default) --- */
if (count($drugs) < 2) {
    out(array('interactions' => null, 'live' => false, 'hint' => 'Usage: api.php?drugs=warfarin,aspirin'));
}

$r = call_api($API_BASE . $EP_ANALYZE, array(
    'patient_id' => 'web_' . substr(md5(implode('|', $drugs)), 0, 8),
    'drugs'      => $drugs,
), $TIMEOUT);

/* Railway unreachable -> null so dashboard uses SAMPLE fallback */
if (!$r['ok']) {
    out(array('interactions' => null, 'live' => false, 'http' => $r['code'], 'error' => $r['error']));
}

/* Translate Railway shape -> Dashboard shape */
$list = array();
$src  = isset($r['data']['interactions']) ? $r['data']['interactions']
        : (isset($r['data']['results']) ? $r['data']['results'] : array());

foreach ($src as $i) {
    if (!is_array($i)) continue;
    $list[] = array(
        'perpetrator' => isset($i['perpetrator']) ? $i['perpetrator'] : (isset($i['drug_a']) ? $i['drug_a'] : '?'),
        'victim'      => isset($i['victim'])      ? $i['victim']      : (isset($i['drug_b']) ? $i['drug_b'] : '?'),
        'mechanism'   => isset($i['mechanism'])   ? $i['mechanism']   : (isset($i['description']) ? $i['description'] : ''),
        'severity'    => isset($i['severity'])    ? $i['severity']    : 'moderate',
    );
}

/* Live but zero findings -> explicit "safe" card */
if (count($list) === 0) {
    $list[] = array(
        'perpetrator' => 'Regimen',
        'victim'      => implode(' + ', $drugs),
        'mechanism'   => 'No clinically significant interaction detected in 2.85M-pair knowledge base',
        'severity'    => 'none',
    );
}

out(array(
    'interactions'       => $list,
    'interactions_found' => isset($r['data']['interactions_found']) ? (int) $r['data']['interactions_found'] : count($src),
    'drugs_analyzed'     => isset($r['data']['drugs_analyzed'])     ? (int) $r['data']['drugs_analyzed']     : count($drugs),
    'harm_propositions'  => isset($r['data']['blackboard_harm_propositions']) ? $r['data']['blackboard_harm_propositions'] : array(),
    'live'               => true,
    'source'             => 'railway_2.85M',
));