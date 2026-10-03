# Site Integrity checkpoint 005 — live source audit

Browser fallback was authorized by Mete. Signed-in WordPress admin is available; no credential changes. Read-only source backups: front-page.php, functions.php, header.php, page.php, index.php, page-ozel-dosyalar.php, inc/ai-english.php, HFCM snippet #1, Command Center panel/shell and Revenue CTA / Global Router main sources.

Findings: EN front-page.php contains hardcoded TR research cards inside its News condition; EN news get_posts has no category and default suppress_filters. TR Research cards exist only in HFCM JavaScript. Legacy English request resolver treats category paths as page names. Header is hardcoded and Revenue CTA v1.3.1 injects Services/Hizmetler after DJ; native nav table lock alone is insufficient. Ana Kumanda parent is oldies-cc-dashboard, panel class Oldies_CC_Panel.

No mutation in this stage. Rollback copies will be included in the persistent deployment package with hashes before installation. Next: source-grounded guard/module code, tests, backup package, live deployment, native scan and frontend verification. No menu rename approved.
