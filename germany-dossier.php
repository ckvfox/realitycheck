<?php
declare(strict_types=1);

require_once __DIR__ . '/analysis-private/real-wages-auth-lib.php';

// Keep the proven authentication workflow available for future private modules.
// This dossier is currently public; change only this flag to restore the login gate.
const RC_DOSSIER_ACCESS_PROTECTION = false;

header('X-Robots-Tag: noindex, nofollow, noarchive', true);
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');
header('Referrer-Policy: no-referrer');
header('X-Frame-Options: DENY');
header('X-Content-Type-Options: nosniff');

$pageLanguage = (($_GET['lang'] ?? '') === 'de') ? 'de' : 'en';
$accessProtectionEnabled = RC_DOSSIER_ACCESS_PROTECTION;
$loadedConfig = null;
$config = rc_rw_config([]);
$now = time();
$csrfToken = '';
$message = '';
$authenticated = !$accessProtectionEnabled;

if ($accessProtectionEnabled) {
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    session_name('RC_REAL_WAGES');
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => '/',
        'secure' => rc_rw_is_https(),
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
    session_start();
    $loadedConfig = rc_rw_load_config(__DIR__);
    $config = rc_rw_config($loadedConfig ?? []);
    $csrfToken = rc_rw_csrf_token($_SESSION);

    if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'logout') {
        if (rc_rw_csrf_valid($_SESSION, $_POST['csrf_token'] ?? null)) {
            $_SESSION = [];
            if (ini_get('session.use_cookies')) {
                $params = session_get_cookie_params();
                setcookie(session_name(), '', [
                    'expires' => time() - 42000,
                    'path' => $params['path'],
                    'domain' => $params['domain'],
                    'secure' => $params['secure'],
                    'httponly' => $params['httponly'],
                    'samesite' => 'Strict',
                ]);
            }
            session_destroy();
            header('Location: ' . strtok((string) $_SERVER['REQUEST_URI'], '?'), true, 303);
            exit;
        }
        $message = 'The request could not be verified. Please reload the page.';
    }

    $authenticated = rc_rw_authenticated($_SESSION, $config, $now);

    if (!$authenticated && $_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'login') {
        $remaining = rc_rw_lock_remaining($_SESSION, $config, $now);
        if (!rc_rw_csrf_valid($_SESSION, $_POST['csrf_token'] ?? null)) {
            $message = 'The request could not be verified. Please reload the page.';
        } elseif ($remaining > 0) {
            $message = 'Too many failed attempts. Please try again in a few minutes.';
        } elseif ($loadedConfig === null || empty($config['password_hash'])) {
            $message = 'The protected area has not yet been configured.';
        } else {
            $password = is_string($_POST['password'] ?? null) ? $_POST['password'] : '';
            if (password_verify($password, (string) $config['password_hash'])) {
                session_regenerate_id(true);
                $_SESSION['rc_rw_authenticated'] = true;
                $_SESSION['rc_rw_last_seen'] = $now;
                $_SESSION['rc_rw_failed_attempts'] = 0;
                unset($_SESSION['rc_rw_locked_until']);
                header('Location: ' . strtok((string) $_SERVER['REQUEST_URI'], '?'), true, 303);
                exit;
            }
            rc_rw_record_failure($_SESSION, $config, $now);
            usleep(max(0, (int) $config['failure_delay_microseconds']));
            $message = 'Incorrect password.';
        }
    }
}

$analysisData = null;
$dataError = '';
$scenarioData = null;
$scenarioDataError = '';
$warStressData = null;
$warStressError = '';
$incomePyramidData = null;
$incomePyramidError = '';
$reformAgendaData = null;
$reformAgendaError = '';
if ($authenticated) {
        $dataPath = __DIR__ . '/analysis-private/' . ($pageLanguage === 'de' ? 'real-wages-data-de.php' : 'real-wages-data.php');
    try {
        if (!is_file($dataPath)) {
            throw new RuntimeException('Datendatei fehlt.');
        }
        $candidate = require $dataPath;
        if (!is_array($candidate)
            || !isset($candidate['meta'], $candidate['trendMeta'], $candidate['germanySeries'], $candidate['comparison'])
            || !is_array($candidate['germanySeries'])
            || !is_array($candidate['comparison'])) {
            throw new RuntimeException('Datendatei hat ein ungültiges Format.');
        }
        $analysisData = $candidate;
    } catch (Throwable $error) {
        $dataError = 'Die Analysedaten konnten nicht geladen werden.';
    }
    try {
        $scenarioPath = __DIR__ . '/analysis-private/' . ($pageLanguage === 'de' ? 'germany-2036-scenarios-de.php' : 'germany-2036-scenarios.php');
        if (!is_file($scenarioPath)) {
            throw new RuntimeException('Szenariodatei fehlt.');
        }
        $scenarioCandidate = require $scenarioPath;
        if (!is_array($scenarioCandidate)
            || !isset($scenarioCandidate['meta'], $scenarioCandidate['scenarios'], $scenarioCandidate['households'], $scenarioCandidate['sources'])) {
            throw new RuntimeException('Szenariodatei hat ein ungültiges Format.');
        }
        $scenarioData = $scenarioCandidate;
    } catch (Throwable $error) {
        $scenarioDataError = 'Die Szenariodaten konnten nicht geladen werden.';
    }
    try {
        $warStressPath = __DIR__ . '/analysis-private/' . ($pageLanguage === 'de' ? 'germany-war-stress-test-de.php' : 'germany-war-stress-test-b2.php');
        if (!is_file($warStressPath)) {
            throw new RuntimeException('War stress-test data is missing.');
        }
        $warStressCandidate = require $warStressPath;
        if (!is_array($warStressCandidate)
            || !isset($warStressCandidate['meta'], $warStressCandidate['phases'], $warStressCandidate['hours72'], $warStressCandidate['households'], $warStressCandidate['sources'])) {
            throw new RuntimeException('War stress-test data has an invalid format.');
        }
        $warStressData = $warStressCandidate;
    } catch (Throwable $error) {
        $warStressError = 'The security stress-test data could not be loaded.';
    }
    try {
        $incomePath = __DIR__ . '/analysis-private/' . ($pageLanguage === 'de' ? 'income-pyramid-data-de.php' : 'income-pyramid-data.php');
        if (!is_file($incomePath)) {
            throw new RuntimeException('Einkommensdaten fehlen.');
        }
        $incomeCandidate = require $incomePath;
        if (!is_array($incomeCandidate)
            || !isset($incomeCandidate['meta'], $incomeCandidate['households'], $incomeCandidate['benchmarkBands'])) {
            throw new RuntimeException('Einkommensdaten haben ein ungültiges Format.');
        }
        $incomePyramidData = $incomeCandidate;
    } catch (Throwable $error) {
        $incomePyramidError = 'The income benchmark data could not be loaded.';
    }
    try {
        $reformPath = __DIR__ . '/analysis-private/germany-reform-agenda.php';
        if (!is_file($reformPath)) {
            throw new RuntimeException('Reform agenda data is missing.');
        }
        $reformCandidate = require $reformPath;
        if (!is_array($reformCandidate)
            || !isset($reformCandidate['meta'], $reformCandidate['chapters'], $reformCandidate['compassLabels'], $reformCandidate['sources'])
            || count($reformCandidate['chapters']) !== 11) {
            throw new RuntimeException('Reform agenda data has an invalid format.');
        }
        $reformDepth = require __DIR__ . '/analysis-private/germany-reform-agenda-depth.php';
        if (!is_array($reformDepth)) {
            throw new RuntimeException('Reform agenda depth data has an invalid format.');
        }
        foreach ($reformCandidate['chapters'] as &$chapter) {
            if (!isset($reformDepth[$chapter['id']])) {
                throw new RuntimeException('A reform chapter depth record is missing.');
            }
            $chapter['depth'] = $reformDepth[$chapter['id']];
        }
        unset($chapter);
        $reformAgendaData = $reformCandidate;
    } catch (Throwable $error) {
        $reformAgendaError = 'The reform agenda could not be loaded.';
    }
}

/**
 * Reuse the curated browser dictionary for the initial server response. This
 * prevents a mixed-language first render and keeps one translation source.
 */
function rc_dossier_de_dictionary(string $scriptPath): array
{
    $source = is_file($scriptPath) ? file_get_contents($scriptPath) : false;
    if (!is_string($source)
        || !preg_match('/const de = new Map\(Object\.entries\(\{(.*?)\}\)\);/su', $source, $block)) {
        return [];
    }
    preg_match_all('/"((?:\\\\.|[^"\\\\])*)"\s*:\s*"((?:\\\\.|[^"\\\\])*)"/u', $block[1], $pairs, PREG_SET_ORDER);
    $dictionary = [];
    foreach ($pairs as $pair) {
        $english = json_decode('"' . $pair[1] . '"', true);
        $german = json_decode('"' . $pair[2] . '"', true);
        if (is_string($english) && is_string($german)) {
            $dictionary[$english] = $german;
        }
    }
    return $dictionary;
}

function rc_dossier_translate_html(string $html, array $dictionary): string
{
    if ($dictionary === [] || !class_exists(DOMDocument::class)) {
        return $html;
    }
    $preservedScripts = [];
    $htmlForTranslation = preg_replace_callback(
        '/<script\b[^>]*>[\s\S]*?<\/script>/iu',
        static function (array $match) use (&$preservedScripts): string {
            $index = count($preservedScripts);
            $preservedScripts[$index] = $match[0];
            return '<!--RC_DOSSIER_SCRIPT_' . $index . '-->';
        },
        $html
    );
    if (!is_string($htmlForTranslation)) {
        return $html;
    }
    $previous = libxml_use_internal_errors(true);
    $document = new DOMDocument('1.0', 'UTF-8');
    $loaded = $document->loadHTML('<?xml encoding="UTF-8">' . $htmlForTranslation, LIBXML_NOERROR | LIBXML_NOWARNING);
    libxml_clear_errors();
    libxml_use_internal_errors($previous);
    if (!$loaded) {
        return $html;
    }
    foreach (iterator_to_array($document->childNodes) as $child) {
        if ($child->nodeType === XML_PI_NODE) {
            $document->removeChild($child);
        }
    }
    $xpath = new DOMXPath($document);
    $nodes = $xpath->query('//text()[normalize-space(.) != "" and not(ancestor::script) and not(ancestor::style) and not(ancestor::*[@lang and local-name() != "html"])]');
    if ($nodes === false) {
        return $html;
    }
    foreach ($nodes as $node) {
        $original = $node->nodeValue ?? '';
        $trimmed = trim($original);
        if (!isset($dictionary[$trimmed])) {
            continue;
        }
        preg_match('/^\s*/u', $original, $leading);
        preg_match('/\s*$/u', $original, $trailing);
        $node->nodeValue = ($leading[0] ?? '') . $dictionary[$trimmed] . ($trailing[0] ?? '');
    }
    $translated = $document->saveHTML() ?: $html;
    foreach ($preservedScripts as $index => $script) {
        $translated = str_replace('<!--RC_DOSSIER_SCRIPT_' . $index . '-->', $script, $translated);
    }
    return $translated;
}

ob_start();
?>
<!DOCTYPE html>
<html lang="<?= $pageLanguage ?>" data-dossier-language="<?= $pageLanguage ?>" data-disable-google-translate>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow, noarchive">
  <meta name="googlebot" content="noindex, nofollow, noarchive">
  <meta name="referrer" content="no-referrer">
  <meta name="rc-build-version" content="20260725-germany-dossier-21">
  <title>Germany Dossier: Prosperity, 2036 Scenarios and Security | RealityCheck</title>
  <link rel="icon" type="image/png" href="favicon.png">
  <link rel="stylesheet" href="style.css?v=20260725-germany-dossier-21">
  <?php if ($authenticated): ?>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.5/dist/chart.umd.min.js" integrity="sha512-TrzZNOcdTjzp6FQnXUlYrt08pfmmNWYCqfjkVK9sJmLrVo/NBuRnTL2FCg4JMjgm2xbn1MVhDbtedqFIppA6cQ==" crossorigin="anonymous" defer></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin="anonymous" defer></script>
  <?php endif; ?>
</head>
<body class="real-wages-page notranslate" translate="no">
  <button id="scroll-top-btn" title="Scroll to top" aria-label="Scroll to top">⬆️</button>
<?php if ($accessProtectionEnabled && !$authenticated): ?>
  <main class="real-wages-login-shell">
    <section class="real-wages-login-card" aria-labelledby="login-title">
      <img src="images/logo.png" alt="RealityCheck" class="real-wages-login-logo">
      <div class="dossier-login-language">
        <span><span lang="en">Language</span><span lang="de">Sprache</span></span>
        <div class="dossier-language-toggle" role="group" aria-label="Language / Sprache">
          <button type="button" data-dossier-language-option="en" aria-pressed="<?= $pageLanguage === 'en' ? 'true' : 'false' ?>"><span class="dossier-language-code" aria-hidden="true"><img src="images/flag/gb.svg" alt=""> EN</span><span>English</span></button>
          <button type="button" data-dossier-language-option="de" aria-pressed="<?= $pageLanguage === 'de' ? 'true' : 'false' ?>"><span class="dossier-language-code" aria-hidden="true"><img src="images/flag/de.svg" alt=""> DE</span><span>Deutsch</span></button>
        </div>
      </div>
      <p class="real-wages-eyebrow">Private working analysis</p>
      <h1 id="login-title">Germany Dossier: Prosperity and Scenarios</h1>
      <p>This data-based analysis and scenario page is password-protected.</p>
      <?php if ($message !== ''): ?>
        <p class="real-wages-alert" role="alert"><?= htmlspecialchars($message, ENT_QUOTES, 'UTF-8') ?></p>
      <?php endif; ?>
      <form method="post" class="real-wages-login-form">
        <input type="hidden" name="action" value="login">
        <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($csrfToken, ENT_QUOTES, 'UTF-8') ?>">
        <label for="password">Password</label>
        <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
        <button type="submit">Open analysis</button>
      </form>
      <p class="real-wages-login-note">An obscure URL is not security. The content is only delivered after server-side authentication.</p>
    </section>
  </main>
<?php else: ?>
  <main class="real-wages-main">
    <?php if ($accessProtectionEnabled): ?>
      <div class="real-wages-toolbar">
        <span>Protected working view</span>
        <form method="post">
          <input type="hidden" name="action" value="logout">
          <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($csrfToken, ENT_QUOTES, 'UTF-8') ?>">
          <button type="submit" class="real-wages-logout">Log out</button>
        </form>
      </div>
    <?php endif; ?>

    <aside class="dossier-language-bar" aria-labelledby="dossier-language-title">
      <div class="dossier-language-copy">
        <strong id="dossier-language-title"><span lang="en">Editorial bilingual edition</span><span lang="de">Redaktionelle zweisprachige Ausgabe</span></strong>
        <p><span lang="en">This specialist dossier is offered in English and German. Its likely audience is particularly German, and automated Google translation is not precise enough for complex scenarios, legal distinctions and policy trade-offs. Both versions are therefore edited here; Google Translate is deliberately disabled on this page.</span><span lang="de">Dieses Spezialdossier wird auf Englisch und Deutsch angeboten. Sein Publikum ist voraussichtlich besonders deutschsprachig, und die automatische Google-Übersetzung ist für komplexe Szenarien, rechtliche Unterscheidungen und politische Zielkonflikte nicht präzise genug. Beide Fassungen werden deshalb hier redaktionell gepflegt; Google Translate ist auf dieser Seite bewusst deaktiviert.</span></p>
      </div>
      <div class="dossier-language-toggle" role="group" aria-label="Language / Sprache">
        <button type="button" data-dossier-language-option="en" aria-pressed="<?= $pageLanguage === 'en' ? 'true' : 'false' ?>"><span class="dossier-language-code" aria-hidden="true"><img src="images/flag/gb.svg" alt=""> EN</span><span>English</span></button>
        <button type="button" data-dossier-language-option="de" aria-pressed="<?= $pageLanguage === 'de' ? 'true' : 'false' ?>"><span class="dossier-language-code" aria-hidden="true"><img src="images/flag/de.svg" alt=""> DE</span><span>Deutsch</span></button>
      </div>
    </aside>

    <section class="real-wages-hero">
      <p class="real-wages-eyebrow">RealityCheck Germany dossier</p>
      <h1>Germany under pressure: prosperity and security towards 2036</h1>
      <p class="real-wages-lead">This dossier combines historical data about Germany, international purchasing-power comparisons and plausible future scenarios. It does not predict a certain collapse. It examines a wealthy country facing slow growth, unequal pressure and security choices that can still change its path.</p>
      <div class="why-germany" aria-labelledby="why-germany-title">
        <h2 id="why-germany-title">Why Germany?</h2>
        <ol>
          <li><strong>Global economic weight.</strong> With nominal GDP of about US$5.05 trillion in 2025, Germany remains one of the world's largest economies.</li>
          <li><strong>European leverage.</strong> It is the EU's most populous member and largest national economy. German choices shape the single market, industrial supply chains, energy networks and Europe's capacity to act.</li>
          <li><strong>A growing security role.</strong> The federal government aims to build the Bundeswehr into Europe's strongest conventional army. That is an ambition and a responsibility — not yet an accomplished fact.</li>
          <li><strong>A democratic counterweight.</strong> In this dossier's value framework, a large, liberal and pluralist Germany can be a source of hope against authoritarian and totalitarian developments. Germany's history makes the democratic and European use of power especially consequential.</li>
          <li><strong>And a personal reason.</strong> I happen to be German. This is the country I know best, whose decisions affect me directly and for whose future I share civic responsibility. That proximity sharpens the analysis, while also making its perspective openly subjective.</li>
        </ol>
        <p class="why-germany-sources">Context: <a href="https://data.worldbank.org/country/germany" target="_blank" rel="noopener noreferrer">World Bank — Germany</a> · <a href="https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20260710-3" target="_blank" rel="noopener noreferrer">Eurostat — EU population 2026</a> · <a href="https://ec.europa.eu/eurostat/databrowser/view/nama_10_gdp/default/table?lang=en" target="_blank" rel="noopener noreferrer">Eurostat — national accounts</a> · <a href="https://www.bundesregierung.de/breg-de/schwerpunkte/schwerpunkt-aussenpolitik-europa-2342408" target="_blank" rel="noopener noreferrer">Federal Government — defence objective</a></p>
      </div>
      <div class="real-wages-scope">
        <strong>Editorial disclosure — this is a values-based and deliberately simplified political narrative.</strong> I see democracy, the rule of law, separation of powers, human rights, a free press, pluralism, minority protection, personal freedom, social solidarity, the welfare state, European cooperation, open science, sustainability and peaceful international cooperation as important foundations of a good society. People who value these things differently will also judge the scenarios differently. Reality is much more complex. Feedback loops, political choices and small events make exact prediction impossible. The ranges are informed estimates, not forecasts. They use serious sources and plausible links between causes and effects.
      </div>
      <p class="scenario-note"><strong>How to read it:</strong> facts and published projections define the starting point. Scenario ranges and probability-like judgements are RealityCheck assumptions. They simplify the most important changes so that people can discuss them. They do not suggest that the real world is simple.</p>
      <nav class="analysis-card-index" aria-label="Germany dossier sections" role="tablist">
        <a id="dossier-tab-prosperity" class="analysis-index-card analysis-index-card--prosperity" href="#germany-prosperity" role="tab" aria-controls="germany-prosperity" aria-selected="true" data-dossier-tab="germany-prosperity">
          <span class="analysis-index-tab">Germany · File 1</span>
          <strong>Prosperity analysis</strong>
          <small>Real wages · purchasing-power context · Income Ladder</small>
        </a>
        <a id="dossier-tab-scenarios" class="analysis-index-card analysis-index-card--scenarios" href="#germany-2036" role="tab" aria-controls="germany-2036" aria-selected="false" tabindex="-1" data-dossier-tab="germany-2036">
          <span class="analysis-index-tab">Germany · File 2</span>
          <strong>2036 Scenarios</strong>
          <small>Three possible futures · assumptions · citizen choices</small>
        </a>
        <a id="dossier-tab-security" class="analysis-index-card analysis-index-card--security" href="#germany-war-stress-test" role="tab" aria-controls="germany-war-stress-test" aria-selected="false" tabindex="-1" data-dossier-tab="germany-war-stress-test">
          <span class="analysis-index-tab">Germany · File 3</span>
          <strong>War Stress Test</strong>
          <small>Escalation chain · preparedness · defence and service</small>
        </a>
        <a id="dossier-tab-reforms" class="analysis-index-card analysis-index-card--reforms" href="#germany-reform-agenda" role="tab" aria-controls="germany-reform-agenda" aria-selected="false" tabindex="-1" data-dossier-tab="germany-reform-agenda">
          <span class="analysis-index-tab">Germany · File 4</span>
          <strong>2036 Reform Agenda</strong>
          <small>International evidence · options · trade-offs</small>
        </a>
      </nav>
    </section>

    <div class="dossier-frame" data-dossier-frame>
    <section id="germany-prosperity" class="analysis-cluster" aria-labelledby="dossier-tab-prosperity" role="tabpanel" tabindex="0" data-dossier-panel>
      <div class="analysis-cluster-heading">
        <p class="real-wages-eyebrow">Germany · Dossier file 1</p>
        <h2 id="prosperity-cluster-title">Prosperity analysis</h2>
        <p>Wage development, Germany's international economic position and the household Income Ladder belong to one question: how high is our material living standard, and how is it changing?</p>
      </div>

    <?php if ($dataError !== ''): ?>
      <section class="real-wages-panel real-wages-alert" role="alert"><?= htmlspecialchars($dataError, ENT_QUOTES, 'UTF-8') ?></section>
    <?php else: ?>
      <section id="germany-analysis" class="real-wages-panel" aria-labelledby="trend-title">
        <div class="real-wages-section-heading">
          <div>
            <p class="real-wages-eyebrow">Germany over time</p>
            <h2 id="trend-title">Official real wage index</h2>
          </div>
          <p id="trend-period" class="real-wages-period"></p>
        </div>
        <p>Index series with base year 2025 = 100. It shows changes in the purchasing power of earnings, not the absolute wage level. The line shows the level and the bars show year-on-year change.</p>
        <div class="real-wages-chart-wrap"><canvas id="real-wages-chart" aria-label="Line chart of Germany's real wage index" role="img"></canvas></div>
        <div id="trend-stats" class="real-wages-stats" aria-live="polite"></div>
        <p id="trend-summary" class="real-wages-summary"></p>
        <aside class="trend-interpretation" aria-labelledby="trend-interpretation-title">
          <p class="real-wages-eyebrow"><span lang="en">Analytical interpretation</span><span lang="de">Analytische Einordnung</span></p>
          <h3 id="trend-interpretation-title"></h3>
          <p id="trend-interpretation-lead"></p>
          <ul id="trend-interpretation-points"></ul>
          <p id="trend-interpretation-conclusion" class="trend-interpretation-conclusion"></p>
        </aside>
        <p id="trend-method-note" class="real-wages-source"></p>
        <p class="real-wages-source">Source: <a id="trend-source" target="_blank" rel="noopener noreferrer"></a></p>
      </section>

      <section class="real-wages-panel" aria-labelledby="context-title">
        <div class="real-wages-section-heading">
          <div>
            <p class="real-wages-eyebrow">Three indicators, three different questions</p>
            <h2 id="context-title">Germany’s economy remains at a high international level — even when wage growth is weak</h2>
          </div>
          <p id="ppp-period" class="real-wages-period"></p>
        </div>
        <div class="real-wages-lenses">
          <article><strong>Real wage index</strong><p>How does the purchasing power of average gross wages change within Germany? The best of these indicators for the wage trend over time.</p></article>
          <article><strong>OECD wage in PPP</strong><p>How high is the average annual gross wage per full-time equivalent? Useful for comparable wage levels, but before tax and without distribution.</p></article>
          <article><strong>GDP per capita in PPP</strong><p>How high is price-adjusted output per resident worldwide? Broad country coverage, but not disposable household income.</p></article>
        </div>
        <p class="real-wages-summary"><strong>A complete household assessment would also need:</strong> median equivalised disposable income after taxes and transfers, housing cost, wealth and distribution. There is no methodologically uniform series covering nearly 200 countries.</p>
        <p class="scenario-note"><strong>How to read the country comparison:</strong> each covered country counts once, regardless of population. Germany’s rank therefore describes its position among national GDP-per-capita values. It is not the income position of German households or of the German population.</p>
        <div id="ppp-status" class="real-wages-status" role="status">Loading global PPP context …</div>
        <div class="real-wages-chart-wrap real-wages-chart-wrap--context"><canvas id="ppp-context-chart" aria-label="Germany in the global GDP-per-capita PPP context" role="img"></canvas></div>
        <div id="ppp-stats" class="real-wages-stats" aria-live="polite"></div>
        <p id="ppp-summary" class="real-wages-summary"></p>
        <p class="real-wages-source"><span lang="en">Source:</span><span lang="de">Quelle:</span> <a href="https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.CD" target="_blank" rel="noopener noreferrer">World Bank – GDP per capita, PPP</a>. <span lang="en">This is context for the economic level, not a substitute for real wages or household income.</span><span lang="de">Dies ist ein Vergleich des wirtschaftlichen Niveaus und kein Ersatz für Reallöhne oder Haushaltseinkommen.</span></p>
      </section>

      <section class="real-wages-panel" aria-labelledby="map-title">
        <div class="real-wages-section-heading">
          <div>
            <p class="real-wages-eyebrow"><span lang="en">International wage comparison</span><span lang="de">Internationaler Lohnvergleich</span></p>
            <h2 id="map-title"><span lang="en">Average annual wages per full-time equivalent compared with Germany</span><span lang="de">Durchschnittliche Jahreslöhne je Vollzeitäquivalent im Vergleich mit Deutschland</span></h2>
          </div>
          <p id="map-period" class="real-wages-period"></p>
        </div>
        <aside class="map-comparison-definition" aria-labelledby="map-comparison-definition-title">
          <strong id="map-comparison-definition-title"><span lang="en">What exactly does this map compare?</span><span lang="de">Was genau vergleicht diese Karte?</span></strong>
          <dl>
            <div><dt><span lang="en">Indicator</span><span lang="de">Kennzahl</span></dt><dd><span lang="en">The OECD average annual wage per full-time-equivalent dependent employee in the total economy.</span><span lang="de">Den durchschnittlichen OECD-Jahreslohn je abhängig beschäftigter Vollzeitkraft in der Gesamtwirtschaft.</span></dd></div>
            <div><dt><span lang="en">Unit</span><span lang="de">Einheit</span></dt><dd><span lang="en">Constant 2025 US dollars converted with purchasing-power parities. This adjusts for different national price levels.</span><span lang="de">Konstante US-Dollar von 2025, umgerechnet mit Kaufkraftparitäten. Dadurch werden unterschiedliche nationale Preisniveaus berücksichtigt.</span></dd></div>
            <div><dt><span lang="en">Germany baseline</span><span lang="de">Deutschland-Basis</span></dt><dd id="map-comparison-baseline"><span lang="en">Germany is the 100% reference. Each colour shows how far a country's average is below or above it.</span><span lang="de">Deutschland ist der 100-Prozent-Bezug. Jede Farbe zeigt, wie weit der Landesdurchschnitt darunter oder darüber liegt.</span></dd></div>
            <div><dt><span lang="en">It does not show</span><span lang="de">Nicht dargestellt werden</span></dt><dd><span lang="en">Net wages, median or typical wages, household income, wage distribution, working hours per person or GDP per capita.</span><span lang="de">Nettolöhne, Median- oder typische Löhne, Haushaltseinkommen, Lohnverteilung, Arbeitsstunden je Person oder das BIP je Einwohner.</span></dd></div>
          </dl>
        </aside>
        <p><span lang="en">Only country averages from the same year and in the same purchasing-power unit are compared. Countries outside this comparable OECD wage dataset remain grey.</span><span lang="de">Verglichen werden nur Landesdurchschnitte aus demselben Jahr und in derselben Kaufkrafteinheit. Länder außerhalb dieser vergleichbaren OECD-Lohnreihe bleiben grau.</span></p>
        <p id="map-coverage-note" class="scenario-note"></p>
        <div id="real-wages-status" class="real-wages-status" role="status">Loading map …</div>
        <div id="real-wages-map" aria-label="World map comparing real average annual wages"></div>
        <div id="map-stats" class="real-wages-stats" aria-live="polite"></div>
        <p id="map-summary" class="real-wages-summary"></p>
        <p class="real-wages-source">Source: <a id="map-source" target="_blank" rel="noopener noreferrer"></a></p>
      </section>
    <?php endif; ?>

    <section id="income-pyramid" class="real-wages-panel income-section" aria-labelledby="income-title">
      <div class="real-wages-section-heading">
        <div>
          <p class="real-wages-eyebrow">Interactive household-income position</p>
          <h2 id="income-title">Where does our household gross income stand?</h2>
        </div>
        <p class="real-wages-period"><span lang="en">Household gross<br>EU-SILC 2025 reference</span><span lang="de">Bruttohaushaltseinkommen<br>EU-SILC-Vergleich 2025</span></p>
      </div>
      <?php if ($incomePyramidError !== ''): ?>
        <p class="real-wages-alert" role="alert"><?= htmlspecialchars($incomePyramidError, ENT_QUOTES, 'UTF-8') ?></p>
      <?php else: ?>
        <p class="scenario-disclaimer"><strong>One figure only:</strong> enter the total annual gross income of the entire household. The comparison changes with the selected household type. It deliberately does not estimate net income because taxes, social insurance, age, transfers and individual circumstances would make that result misleading.</p>
        <div class="income-layout">
          <form class="income-form">
            <div class="income-household-field"><label for="income-household">Household type</label><select id="income-household" data-income-household aria-describedby="income-household-help"></select><p id="income-household-help" class="income-household-help" data-income-household-help></p></div>
            <div><label for="income-gross">Total annual household gross</label><div class="income-input-unit"><input id="income-gross" data-income-gross type="number" min="0" step="500" inputmode="numeric" placeholder="e.g. 96000"><span>€</span></div></div>
            <p class="income-form-note">Use the combined annual gross income of all household members, including bonuses and other gross income sources where applicable.</p>
          </form>
          <div>
            <div class="income-pyramid" data-income-pyramid aria-label="Household gross-income benchmark ladder"></div>
            <p class="income-pyramid-note"><span lang="en">This is a benchmark ladder, not a percentile pyramid. The bands show transparent distances from the official EU-SILC average for the selected household type. “DINKs” is a short label only: the source identifies two adults without children, but not whether both adults earn an income.</span><span lang="de">Dies ist eine Vergleichsleiter und keine Perzentilpyramide. Die Bereiche zeigen transparente Abstände zum amtlichen EU-SILC-Durchschnitt des gewählten Haushaltstyps. „DINKs“ ist nur eine Kurzbezeichnung: Die Quelle erkennt zwei Erwachsene ohne Kinder, aber nicht, ob beide ein Einkommen erzielen.</span></p>
          </div>
        </div>
        <div class="income-household-comparison" data-income-household-result></div>
        <p class="real-wages-status" data-income-status role="status"></p>
        <details class="scenario-method">
          <summary>Data basis and limits</summary>
          <p><span lang="en">The comparison uses Destatis EU-SILC 2025. It distinguishes six household types more precisely than the previous size-only EVS comparison. It does not separate the number of children, the number of earners, regional prices, housing costs, taxes, debt or wealth. It is therefore a useful orientation, not a social-class diagnosis.</span><span lang="de">Der Vergleich nutzt EU-SILC 2025 von Destatis. Die Quelle unterscheidet sechs Haushaltstypen genauer als der frühere EVS-Vergleich nur nach Personenzahl. Sie trennt jedoch weder Kinderzahl noch Zahl der Erwerbstätigen und berücksichtigt keine regionalen Preise, Wohnkosten, Steuern, Schulden oder Vermögen. Die Einordnung ist deshalb eine Orientierung und keine Diagnose der sozialen Schicht.</span></p>
          <ul>
          <?php foreach ($incomePyramidData['sources'] as $source): ?>
            <li><a href="<?= htmlspecialchars($source['url'], ENT_QUOTES, 'UTF-8') ?>" target="_blank" rel="noopener noreferrer"><?= htmlspecialchars($source['label'], ENT_QUOTES, 'UTF-8') ?></a>: <?= htmlspecialchars($source['use'], ENT_QUOTES, 'UTF-8') ?></li>
          <?php endforeach; ?>
          </ul>
        </details>
      <?php endif; ?>
    </section>

    <section class="real-wages-panel real-wages-method">
      <h2>Method note</h2>
      <p>The chart uses the official Destatis real wage index; an index value is not an absolute amount of money. The OECD map indicator is an average per full-time equivalent. It measures a real wage level, but neither the median wage nor disposable household income. The map covers countries in the OECD source, not automatically every country in the world.</p>
    </section>
    </section>

    <section id="germany-2036" class="real-wages-panel scenario-section" aria-labelledby="dossier-tab-scenarios" role="tabpanel" tabindex="0" data-dossier-panel>
      <div class="real-wages-section-heading">
        <div>
          <p class="real-wages-eyebrow">Germany · Dossier file 2</p>
          <h2 id="scenario-title">Germany 2036 — three possible futures</h2>
        </div>
        <p class="real-wages-period">Horizon 2026–2036<br>Sources reviewed <?= $scenarioData !== null ? htmlspecialchars($scenarioData['meta']['updatedAt'], ENT_QUOTES, 'UTF-8') : '–' ?></p>
      </div>
      <?php if ($scenarioDataError !== ''): ?>
        <p class="real-wages-alert" role="alert"><?= htmlspecialchars($scenarioDataError, ENT_QUOTES, 'UTF-8') ?></p>
      <?php else: ?>
        <p class="scenario-disclaimer" data-scenario-status></p>
        <div class="scenario-strategy-grid" aria-label="Strategic principles across all scenarios">
        <?php foreach ($scenarioData['strategicPrinciples'] as $principle): ?>
          <article><h3><?= htmlspecialchars($principle['title'], ENT_QUOTES, 'UTF-8') ?></h3><p><?= htmlspecialchars($principle['text'], ENT_QUOTES, 'UTF-8') ?></p></article>
        <?php endforeach; ?>
        </div>
        <div class="scenario-tabs" data-scenario-tabs aria-label="Choose scenario"></div>
        <div class="scenario-intro">
          <div>
            <p class="real-wages-eyebrow">The scenario narrative</p>
            <h3 data-scenario-name></h3>
            <p class="scenario-story" data-scenario-story></p>
            <p class="scenario-premise"><strong>Core premise:</strong> <span data-scenario-premise></span></p>
            <h4>What drives this story</h4>
            <ul class="scenario-drivers" data-drivers></ul>
          </div>
          <div class="scenario-chart scenario-chart--radar"><canvas data-chart="radar" aria-label="Robustheitsprofil des aktiven Szenarios" role="img"></canvas></div>
        </div>

        <h3>Macro effects in 2036</h3>
        <div class="scenario-metrics" data-metric-cards aria-live="polite"></div>

        <div class="scenario-grid">
          <div>
            <h3>All three base scenarios</h3>
            <p class="scenario-note">Energy and climate are burden indices: lower is better. Bars show midpoints; tooltips show the modelled range.</p>
            <div class="scenario-chart"><canvas data-chart="comparison" aria-label="Vergleich der drei Szenarien" role="img"></canvas></div>
          </div>
          <div>
            <h3>Schematic path</h3>
            <p class="scenario-note">Dashed lines connect only four support years. They do not claim a smooth annual trajectory.</p>
            <div class="scenario-chart"><canvas data-chart="timeline" aria-label="Schematische Entwicklung bis 2036" role="img"></canvas></div>
          </div>
        </div>

        <details class="scenario-controls">
          <summary>Change assumptions</summary>
          <p>The controls are a sensitivity analysis. They change the index ranges deterministically; they do not estimate probabilities.</p>
          <div class="scenario-sliders" data-scenario-sliders></div>
          <button type="button" class="scenario-reset" data-reset>Reset to base scenario</button>
        </details>

        <div class="scenario-household">
          <div>
            <label for="scenario-household"><strong>What could this mean for a household?</strong></label>
            <select id="scenario-household" data-household-select></select>
          </div>
          <div class="scenario-household-result" data-household-result></div>
          <dl>
            <div><dt>Daily life</dt><dd data-household-daily></dd></div>
            <div><dt>Taxes and social contributions</dt><dd data-household-tax></dd></div>
            <div><dt>Energy and mobility</dt><dd data-household-energy></dd></div>
            <div><dt>Housing and insurance</dt><dd data-household-housing></dd></div>
            <div><dt>Transfers and provision</dt><dd data-household-transfers></dd></div>
            <div><dt>Employment risk</dt><dd data-household-risk></dd></div>
            <div><dt>Training</dt><dd data-household-training></dd></div>
            <div><dt>Helpful policy</dt><dd data-household-help></dd></div>
          </dl>
        </div>

        <div class="scenario-actions">
          <h3>Robust measures — useful in all three scenarios</h3>
          <div class="scenario-table-wrap"><table><thead><tr><th>Area</th><th>Measure</th><th>Effect</th><th>Time</th><th>Cost</th><th>Value in stress case</th></tr></thead><tbody>
          <?php foreach ($scenarioData['measures'] as $measure): ?>
            <tr><td><?= htmlspecialchars($measure['area'], ENT_QUOTES, 'UTF-8') ?></td><td><?= htmlspecialchars($measure['measure'], ENT_QUOTES, 'UTF-8') ?></td><td><?= htmlspecialchars($measure['effect'], ENT_QUOTES, 'UTF-8') ?></td><td><?= htmlspecialchars($measure['duration'], ENT_QUOTES, 'UTF-8') ?></td><td><?= htmlspecialchars($measure['cost'], ENT_QUOTES, 'UTF-8') ?></td><td><?= htmlspecialchars($measure['worst'], ENT_QUOTES, 'UTF-8') ?></td></tr>
          <?php endforeach; ?>
          </tbody></table></div>
        </div>

        <div class="scenario-citizens">
          <h3>What can I do as a citizen?</h3>
          <p>Individual action cannot replace effective infrastructure, security, social or industrial policy. It can strengthen demand, local resilience, occupational adaptability and democratic pressure for delivery.</p>
          <div class="scenario-citizen-grid">
          <?php foreach ($scenarioData['citizenActions'] as $action): ?>
            <article>
              <h4><?= htmlspecialchars($action['lever'], ENT_QUOTES, 'UTF-8') ?></h4>
              <p><?= htmlspecialchars($action['action'], ENT_QUOTES, 'UTF-8') ?></p>
              <dl><dt>Supports</dt><dd><?= htmlspecialchars($action['supports'], ENT_QUOTES, 'UTF-8') ?></dd><dt>Helps prevent</dt><dd><?= htmlspecialchars($action['prevents'], ENT_QUOTES, 'UTF-8') ?></dd></dl>
            </article>
          <?php endforeach; ?>
          </div>
        </div>

        <details id="scenario-method" class="scenario-method">
          <summary>Sources and assumptions matrix</summary>
          <p><strong>Reading key:</strong> observations describe the past, official projections extend published assumptions and institutional analyses support causal directions. The 2036 ranges, slider weights and stress events are RealityCheck assumptions.</p>
          <div class="scenario-table-wrap"><table><thead><tr><th>Area</th><th>Type</th><th>Finding</th><th>Source</th><th>Use</th></tr></thead><tbody>
          <?php foreach ($scenarioData['sources'] as $source): ?>
            <tr><td><?= htmlspecialchars($source['area'], ENT_QUOTES, 'UTF-8') ?></td><td><?= htmlspecialchars($source['kind'], ENT_QUOTES, 'UTF-8') ?></td><td><?= htmlspecialchars($source['claim'], ENT_QUOTES, 'UTF-8') ?></td><td><a href="<?= htmlspecialchars($source['url'], ENT_QUOTES, 'UTF-8') ?>" target="_blank" rel="noopener noreferrer"><?= htmlspecialchars($source['source'], ENT_QUOTES, 'UTF-8') ?></a></td><td><?= htmlspecialchars($source['use'], ENT_QUOTES, 'UTF-8') ?></td></tr>
          <?php endforeach; ?>
          </tbody></table></div>
        </details>
      <?php endif; ?>
    </section>

    <section id="germany-war-stress-test" class="real-wages-panel war-stress-section" aria-labelledby="dossier-tab-security" role="tabpanel" tabindex="0" data-dossier-panel>
      <div class="real-wages-section-heading">
        <div>
          <p class="real-wages-eyebrow">Germany · Dossier file 3</p>
          <h2 id="war-stress-title">Special scenario: Germany at War</h2>
          <p class="war-stress-subtitle">A security-policy stress test — not a forecast</p>
        </div>
        <p class="real-wages-period">No probability<br>Reviewed <?= $warStressData !== null ? htmlspecialchars($warStressData['meta']['updatedAt'], ENT_QUOTES, 'UTF-8') : '–' ?></p>
      </div>
      <?php if ($warStressError !== ''): ?>
        <p class="real-wages-alert" role="alert"><?= htmlspecialchars($warStressError, ENT_QUOTES, 'UTF-8') ?></p>
      <?php else: ?>
        <div class="war-stress-warning" role="note">
          <strong><?= htmlspecialchars($warStressData['meta']['warning'], ENT_QUOTES, 'UTF-8') ?></strong>
          <span><?= htmlspecialchars($warStressData['meta']['noProbability'], ENT_QUOTES, 'UTF-8') ?></span>
        </div>
        <div class="war-stress-entry">
          <div>
            <h3>Why examine an extreme case?</h3>
            <p>The purpose is to identify where deterrence, political cohesion, infrastructure protection and civil preparedness can interrupt escalation. It does not claim that Russia will attack Germany or that war is unavoidable.</p>
            <p class="scenario-note"><?= htmlspecialchars($warStressData['meta']['inspiration'], ENT_QUOTES, 'UTF-8') ?></p>
          </div>
          <div>
            <h3>Real threat versus fictional escalation</h3>
            <p>Observed hybrid activity and official threat assessments form the starting point. A Russian victory in Ukraine, a limited attack on NATO and open strikes on Germany are explicitly set assumptions.</p>
          </div>
        </div>
        <aside class="war-strategic-doctrine" aria-label="Normative security position">
          <h3><?= htmlspecialchars($warStressData['strategicDoctrine']['headline'], ENT_QUOTES, 'UTF-8') ?></h3>
          <p><?= htmlspecialchars($warStressData['strategicDoctrine']['text'], ENT_QUOTES, 'UTF-8') ?></p>
          <p><strong>Trade:</strong> <?= htmlspecialchars($warStressData['strategicDoctrine']['trade'], ENT_QUOTES, 'UTF-8') ?></p>
          <p><strong>Energy:</strong> <?= htmlspecialchars($warStressData['strategicDoctrine']['energy'], ENT_QUOTES, 'UTF-8') ?></p>
        </aside>
        <div class="war-stress-evidence-legend" data-war-evidence-legend aria-label="Evidence labels"></div>
        <button type="button" class="war-stress-activate" data-war-activate aria-expanded="false" aria-controls="war-stress-content">Run the stress test</button>
        <div id="war-stress-content" class="war-stress-content" data-war-content hidden tabindex="-1">
          <h3 data-war-content-title>The seven-phase escalation path</h3>
          <p class="scenario-note">Every phase names both the assumed escalation and an intervention point. No real target list, coordinates, tactical instructions, casualty figures or attack frequencies are shown.</p>
          <div class="war-stress-timeline" data-war-timeline></div>

          <section class="war-stress-block" aria-labelledby="war-prevention-title">
            <h3 id="war-prevention-title">What could have interrupted the chain?</h3>
            <p>Prevention is broader than military capability. The same chain has diplomatic, economic, societal and civil-protection off-ramps.</p>
            <div class="war-prevention-grid" data-war-prevention></div>
          </section>

          <section class="war-stress-block" aria-labelledby="war-72-title">
            <h3 id="war-72-title">The first 72 hours in Germany</h3>
            <p>Illustrative consequences after the fictional open attack. Personal preparation follows BBK guidance only.</p>
            <div class="war-72-grid" data-war-hours></div>
            <aside class="war-preparedness" data-war-preparedness></aside>
          </section>

          <section class="war-stress-block" aria-labelledby="war-household-title">
            <h3 id="war-household-title">What could this mean for me?</h3>
            <label for="war-household-select"><strong>Select a household perspective</strong></label>
            <select id="war-household-select" data-war-household></select>
            <div class="war-household-result" data-war-household-result aria-live="polite"></div>
          </section>

          <section class="war-stress-block" aria-labelledby="war-debate-title">
            <h3 id="war-debate-title">Does rearmament make war more likely?</h3>
            <div class="war-debate-grid" data-war-debate></div>
            <p class="war-debate-conclusion" data-war-debate-conclusion></p>
          </section>

          <section class="war-stress-block" aria-labelledby="war-objections-title">
            <h3 id="war-objections-title">Serious objections and responses</h3>
            <p>Pacifist and critical positions are treated as legitimate arguments, not as disloyalty.</p>
            <div class="war-objections" data-war-objections></div>
          </section>

          <section class="war-stress-block" aria-labelledby="war-people-title">
            <h3 id="war-people-title">Why defence needs people</h3>
            <ul class="war-role-list" data-war-roles></ul>
            <section class="war-service-debate" aria-labelledby="war-service-debate-title">
              <h4 id="war-service-debate-title" data-war-service-title></h4>
              <p data-war-service-intro></p>
              <p class="war-service-learning" data-war-service-learning></p>
              <div class="war-service-comparison" data-war-service-comparison></div>
              <h5 data-war-service-enforcement-title></h5>
              <ul class="war-service-enforcement" data-war-service-enforcement></ul>
              <p class="war-debate-conclusion" data-war-service-conclusion></p>
              <div class="war-refusal-paradox">
                <h5 data-war-refusal-title></h5>
                <p data-war-refusal-text></p>
                <p><strong>Evidence:</strong> <span data-war-refusal-evidence></span></p>
                <p class="scenario-note"><strong>Limit:</strong> <span data-war-refusal-limit></span></p>
                <p class="war-refusal-sources" data-war-refusal-sources></p>
              </div>
            </section>
            <h4>Five personnel models at a glance</h4>
            <div class="scenario-table-wrap"><table class="war-service-table"><thead><tr><th>Model</th><th>Military effect</th><th>Build-up speed</th><th>Cost</th><th>Freedom</th><th>Fairness</th><th>Specialists</th><th>Reserve / civil protection</th><th>Education and labour</th></tr></thead><tbody data-war-service-models></tbody></table></div>
            <h4>Democratic safeguards</h4>
            <ul data-war-safeguards></ul>

            <section class="war-conscription-analysis" aria-labelledby="war-conscription-title">
              <h4 id="war-conscription-title" data-war-conscription-title></h4>
              <p data-war-conscription-definition></p>
              <p class="real-wages-status" data-war-conscription-status role="status">The world map loads when this stress test is opened.</p>
              <div id="war-conscription-map" aria-label="World map comparing active conscription and V-Dem regime classification"></div>
              <div class="war-conscription-stats" data-war-conscription-stats aria-live="polite"></div>
              <p class="war-debate-conclusion" data-war-conscription-conclusion></p>
              <p class="scenario-note" data-war-conscription-method></p>
            </section>
          </section>

          <section class="war-stress-block" aria-labelledby="war-history-title">
            <h3 id="war-history-title">Historical comparisons — clues, not proofs</h3>
            <div class="war-history-grid" data-war-history></div>
          </section>

          <details class="scenario-method war-source-method">
            <summary>Evidence and assumption matrix</summary>
            <p>Sources support starting conditions, legal rules and causal mechanisms. They do not estimate the fictional seven-phase chain.</p>
            <div class="scenario-table-wrap"><table><thead><tr><th>Evidence type</th><th>Institution / author</th><th>Source</th><th>Finding used here</th></tr></thead><tbody data-war-sources></tbody></table></div>
          </details>

          <footer class="war-stress-closing" data-war-closing></footer>
        </div>
      <?php endif; ?>
    </section>

    <section id="germany-reform-agenda" class="real-wages-panel reform-agenda-section" aria-labelledby="dossier-tab-reforms" role="tabpanel" tabindex="0" data-dossier-panel>
      <?php if ($reformAgendaError !== ''): ?>
        <p class="real-wages-alert" role="alert"><?= htmlspecialchars($reformAgendaError, ENT_QUOTES, 'UTF-8') ?></p>
      <?php else: ?>
        <header class="reform-agenda-hero">
          <p class="real-wages-eyebrow"><span lang="en">Germany · Dossier file 4</span><span lang="de">Deutschland · Dossierakte 4</span></p>
          <h2><span lang="en">Germany 2036 — Reform Agenda</span><span lang="de">Deutschland 2036 – Reformagenda</span></h2>
          <p class="reform-agenda-subtitle"><span lang="en">International best practices for a future-ready Germany</span><span lang="de">Internationale Best Practices für ein zukunftsfähiges Deutschland</span></p>
          <p><span lang="en">The scenarios describe what might happen. This file asks a different question: which reforms could increase the probability of a successful Germany in 2036? It compares mechanisms used by democratic industrialised countries without endorsing a party or pretending that foreign systems can simply be copied.</span><span lang="de">Die Szenarien beschreiben, was geschehen könnte. Diese Akte stellt eine andere Frage: Welche Reformen könnten die Wahrscheinlichkeit eines erfolgreichen Deutschlands im Jahr 2036 erhöhen? Sie vergleicht Mechanismen demokratischer Industriestaaten, ohne eine Partei zu unterstützen oder vorzugeben, ausländische Systeme ließen sich einfach kopieren.</span></p>
          <div class="real-wages-scope"><strong><span lang="en">Not opinion. Evidence, comparisons and international experience.</span><span lang="de">Nicht Meinung. Sondern Fakten, Vergleiche und internationale Erfahrungen.</span></strong> <span lang="en">Every chapter uses the same six-part structure, presents opportunities and risks, and links to its evidence base.</span><span lang="de">Jedes Kapitel folgt derselben sechsteiligen Struktur, zeigt Chancen und Risiken und verlinkt seine Evidenzbasis.</span></div>
          <p class="scenario-note"><strong><span lang="en">Method:</span><span lang="de">Methode:</span></strong> <span lang="en"><?= htmlspecialchars($reformAgendaData['meta']['method']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($reformAgendaData['meta']['method']['de'], ENT_QUOTES, 'UTF-8') ?></span></p>
        </header>

        <nav class="reform-topic-nav" aria-label="Reform chapters / Reformkapitel">
          <?php foreach ($reformAgendaData['chapters'] as $chapter): ?>
            <a href="#reform-<?= htmlspecialchars($chapter['id'], ENT_QUOTES, 'UTF-8') ?>"><span aria-hidden="true"><?= htmlspecialchars($chapter['icon'], ENT_QUOTES, 'UTF-8') ?></span><span lang="en"><?= htmlspecialchars($chapter['title']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['title']['de'], ENT_QUOTES, 'UTF-8') ?></span></a>
          <?php endforeach; ?>
        </nav>

        <div class="reform-chapter-list">
          <?php foreach ($reformAgendaData['chapters'] as $chapter): ?>
            <article id="reform-<?= htmlspecialchars($chapter['id'], ENT_QUOTES, 'UTF-8') ?>" class="reform-chapter">
              <header class="reform-chapter-heading"><span class="reform-chapter-number" aria-hidden="true"><?= htmlspecialchars($chapter['icon'], ENT_QUOTES, 'UTF-8') ?></span><div><p class="real-wages-eyebrow"><span lang="en">Reform field</span><span lang="de">Reformfeld</span></p><h3><span lang="en"><?= htmlspecialchars($chapter['title']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['title']['de'], ENT_QUOTES, 'UTF-8') ?></span></h3></div></header>

              <div class="reform-standard-grid">
                <section><h4><span aria-hidden="true">1</span> <span lang="en">Problem and 2036 outlook</span><span lang="de">Problem und Ausblick bis 2036</span></h4><p class="reform-summary"><span lang="en"><?= htmlspecialchars($chapter['problem']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['problem']['de'], ENT_QUOTES, 'UTF-8') ?></span></p><?php foreach ($chapter['depth']['problemDetail']['en'] as $index => $paragraph): ?><p><span lang="en"><?= htmlspecialchars($paragraph, ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['depth']['problemDetail']['de'][$index], ENT_QUOTES, 'UTF-8') ?></span></p><?php endforeach; ?><p class="reform-outlook"><strong><span lang="en">What this means by 2036:</span><span lang="de">Was das bis 2036 bedeutet:</span></strong> <span lang="en"><?= htmlspecialchars($chapter['depth']['outlook']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['depth']['outlook']['de'], ENT_QUOTES, 'UTF-8') ?></span></p></section>
                <section><h4><span aria-hidden="true">2</span> <span lang="en">Germany today</span><span lang="de">Deutschland heute</span></h4><p class="reform-summary"><span lang="en"><?= htmlspecialchars($chapter['germany']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['germany']['de'], ENT_QUOTES, 'UTF-8') ?></span></p><?php foreach ($chapter['depth']['germanyDetail']['en'] as $index => $paragraph): ?><p><span lang="en"><?= htmlspecialchars($paragraph, ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['depth']['germanyDetail']['de'][$index], ENT_QUOTES, 'UTF-8') ?></span></p><?php endforeach; ?></section>
              </div>

              <section class="reform-best-practices">
                <h4><span aria-hidden="true">3</span> <span lang="en">International best practices</span><span lang="de">Internationale Best Practices</span></h4>
                <div class="reform-case-grid">
                  <?php foreach ($chapter['cases'] as $caseIndex => $case): $caseDepth = $chapter['depth']['caseDetails'][$caseIndex]; ?>
                    <article><h5><span lang="en"><?= htmlspecialchars($case['country']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($case['country']['de'], ENT_QUOTES, 'UTF-8') ?></span></h5><p><strong><span lang="en">Starting point:</span><span lang="de">Ausgangslage:</span></strong> <span lang="en"><?= htmlspecialchars($caseDepth['starting']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($caseDepth['starting']['de'], ENT_QUOTES, 'UTF-8') ?></span></p><p><strong><span lang="en">Reform and implementation:</span><span lang="de">Reform und Umsetzung:</span></strong> <span lang="en"><?= htmlspecialchars($caseDepth['implementation']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($caseDepth['implementation']['de'], ENT_QUOTES, 'UTF-8') ?></span></p><p><strong><span lang="en">Observed result:</span><span lang="de">Beobachtetes Ergebnis:</span></strong> <span lang="en"><?= htmlspecialchars($caseDepth['results']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($caseDepth['results']['de'], ENT_QUOTES, 'UTF-8') ?></span></p><p><strong><span lang="en">Transfer to Germany:</span><span lang="de">Übertragbarkeit auf Deutschland:</span></strong> <span lang="en"><?= htmlspecialchars($caseDepth['transfer']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($caseDepth['transfer']['de'], ENT_QUOTES, 'UTF-8') ?></span></p></article>
                  <?php endforeach; ?>
                </div>
              </section>

              <div class="reform-standard-grid">
                <section><h4><span aria-hidden="true">4</span> <span lang="en">Possible reform options</span><span lang="de">Mögliche Reformoptionen</span></h4><ul><?php foreach ($chapter['options']['en'] as $index => $option): ?><li><span lang="en"><?= htmlspecialchars($option, ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['options']['de'][$index], ENT_QUOTES, 'UTF-8') ?></span></li><?php endforeach; ?></ul></section>
                <section><h4><span aria-hidden="true">5</span> <span lang="en">Opportunities, risks and conditions</span><span lang="de">Chancen, Risiken und Voraussetzungen</span></h4><p><span lang="en"><?= htmlspecialchars($chapter['balance']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['balance']['de'], ENT_QUOTES, 'UTF-8') ?></span></p><h5><span lang="en">Conditions for success</span><span lang="de">Voraussetzungen für Erfolg</span></h5><ul><?php foreach ($chapter['depth']['prerequisites']['en'] as $index => $item): ?><li><span lang="en"><?= htmlspecialchars($item, ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['depth']['prerequisites']['de'][$index], ENT_QUOTES, 'UTF-8') ?></span></li><?php endforeach; ?></ul></section>
              </div>

              <section class="reform-conclusion"><h4><span aria-hidden="true">6</span> <span lang="en">RealityCheck conclusion</span><span lang="de">RealityCheck-Fazit</span></h4><p><span lang="en"><?= htmlspecialchars($chapter['conclusion']['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($chapter['conclusion']['de'], ENT_QUOTES, 'UTF-8') ?></span></p></section>

              <section class="reform-compass" aria-label="Germany 2036 compass / Deutschland-2036-Kompass">
                <div class="reform-compass-heading"><h4><span lang="en">Germany 2036 Compass</span><span lang="de">Deutschland-2036-Kompass</span></h4><p><span lang="en">Editorial assessment, 1 (low/short) to 5 (high/long).</span><span lang="de">Redaktionelle Bewertung, 1 (niedrig/kurz) bis 5 (hoch/lang).</span></p></div>
                <div class="reform-compass-grid">
                  <?php foreach ($reformAgendaData['compassLabels'] as $index => $label): $score = (int) $chapter['compass'][$index]; ?>
                    <div><span><span lang="en"><?= htmlspecialchars($label['en'], ENT_QUOTES, 'UTF-8') ?></span><span lang="de"><?= htmlspecialchars($label['de'], ENT_QUOTES, 'UTF-8') ?></span></span><meter min="1" max="5" value="<?= $score ?>"><?= $score ?> / 5</meter><strong><?= $score ?>/5</strong></div>
                  <?php endforeach; ?>
                </div>
              </section>

              <p class="reform-chapter-sources"><strong><span lang="en">Sources:</span><span lang="de">Quellen:</span></strong>
                <?php foreach ($chapter['sources'] as $index => $sourceId): $source = $reformAgendaData['sources'][$sourceId]; ?><?= $index > 0 ? ' · ' : '' ?><a href="<?= htmlspecialchars($source['url'], ENT_QUOTES, 'UTF-8') ?>" target="_blank" rel="noopener noreferrer"><?= htmlspecialchars($source['organisation'] . ' — ' . $source['title'], ENT_QUOTES, 'UTF-8') ?></a><?php endforeach; ?>
              </p>
            </article>
          <?php endforeach; ?>
        </div>

        <details class="scenario-method reform-source-matrix"><summary><span lang="en">Complete source register and editorial limits</span><span lang="de">Vollständiges Quellenverzeichnis und redaktionelle Grenzen</span></summary><p><span lang="en">The linked institutions support the diagnosed mechanisms and comparisons. The 1–5 compass values are transparent RealityCheck judgements, not source scores or predictions.</span><span lang="de">Die verlinkten Institutionen stützen die beschriebenen Mechanismen und Vergleiche. Die Kompasswerte von 1 bis 5 sind transparente RealityCheck-Einschätzungen, keine Quellenwerte oder Prognosen.</span></p><ul><?php foreach ($reformAgendaData['sources'] as $source): ?><li><a href="<?= htmlspecialchars($source['url'], ENT_QUOTES, 'UTF-8') ?>" target="_blank" rel="noopener noreferrer"><?= htmlspecialchars($source['organisation'] . ' — ' . $source['title'], ENT_QUOTES, 'UTF-8') ?></a></li><?php endforeach; ?></ul></details>
      <?php endif; ?>
    </section>
    </div>

  </main>

  <?php if ($analysisData !== null): ?>
    <script id="real-wages-data" type="application/json"><?= json_encode($analysisData, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR) ?></script>
    <script src="scripts/core.js?v=20260725-dossier-public-bilingual-2" defer></script>
    <script src="scripts/page_real_wages_analysis.js?v=20260725-wage-analysis-3" defer></script>
  <?php endif; ?>
  <?php if ($scenarioData !== null): ?>
    <script id="germany-2036-data" type="application/json"><?= json_encode($scenarioData, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR) ?></script>
    <script src="scripts/page_germany_2036_scenarios.js?v=20260725-dossier-bilingual-1" defer></script>
  <?php endif; ?>
  <?php if ($warStressData !== null): ?>
    <script id="germany-war-stress-data" type="application/json"><?= json_encode($warStressData, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR) ?></script>
    <script src="scripts/page_germany_war_stress_test.js?v=20260725-dossier-bilingual-1" defer></script>
  <?php endif; ?>
  <?php if ($incomePyramidData !== null): ?>
    <script id="income-pyramid-data" type="application/json"><?= json_encode($incomePyramidData, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR) ?></script>
    <script src="scripts/page_income_pyramid.js?v=20260725-household-help-3" defer></script>
  <?php endif; ?>
  <script src="scripts/page_germany_dossier.js?v=20260725-dossier-tabs-3" defer></script>
<?php endif; ?>
  <script src="scripts/page_germany_dossier_i18n.js?v=20260725-dossier-i18n-4" defer></script>
</body>
</html>
<?php
$renderedPage = (string) ob_get_clean();
if ($pageLanguage === 'de') {
    $renderedPage = rc_dossier_translate_html($renderedPage, rc_dossier_de_dictionary(__DIR__ . '/scripts/page_germany_dossier_i18n.js'));
}
echo $renderedPage;
?>
