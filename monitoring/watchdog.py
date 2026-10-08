"""Oldies Radyo: read-only audit of GitHub Actions, optional deduplicated issue alerts."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKFLOW_SELF = '.github/workflows/oldies-watchdog.yml'
BAD_CONCLUSIONS = {'failure', 'timed_out', 'action_required', 'startup_failure'}


def when(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def hours_since(value: str, now: datetime) -> float:
    return (now - when(value)).total_seconds() / 3600


class GitHub:
    def __init__(self, repo: str, token: str, api_url: str = 'https://api.github.com'):
        self.repo = repo
        self.token = token
        self.base = f"{api_url.rstrip('/')}/repos/{repo}"

    def request(self, path: str, *, method: str = 'GET', data=None):
        body = None if data is None else json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            self.base + path,
            data=body,
            method=method,
            headers={
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'User-Agent': 'oldies-watchdog/1.0',
                **({'Content-Type': 'application/json'} if body else {}),
            },
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.load(response)


def collect(api, config: dict, now: datetime):
    workflows = []
    for page in range(1, 11):
        batch = api.request(f'/actions/workflows?per_page=100&page={page}').get('workflows', [])
        workflows.extend(batch)
        if len(batch) < 100:
            break
    findings, healthy, unchecked = [], [], []
    freshness = config.get('expected_freshness_hours', {})
    stalled_hours = float(config.get('stalled_hours', 3))
    active_paths = set()
    for workflow in workflows:
        path = workflow['path']
        if workflow.get('state') != 'active' or path == WORKFLOW_SELF:
            continue
        active_paths.add(path)
        runs = api.request(f"/actions/workflows/{workflow['id']}/runs?per_page=1").get('workflow_runs', [])
        expected = freshness.get(path)
        if not runs:
            if expected is not None:
                findings.append({'path': path, 'name': workflow['name'], 'reason': 'never_run', 'run_id': None, 'url': ''})
            else:
                unchecked.append(path)
            continue
        run = runs[0]
        age = hours_since(run.get('run_started_at') or run['created_at'], now)
        reason = None
        if run.get('status') == 'completed' and run.get('conclusion') in BAD_CONCLUSIONS:
            reason = 'failed_run'
        elif run.get('status') in ('in_progress', 'queued', 'waiting', 'pending') and age > stalled_hours:
            reason = 'stalled_run'
        elif expected is not None and age > float(expected):
            reason = 'late_run'
        if reason:
            findings.append({'path': path, 'name': workflow['name'], 'reason': reason,
                             'run_id': run['id'], 'url': run.get('html_url', '')})
        else:
            healthy.append(path)
    for path in freshness:
        if path not in active_paths:
            findings.append({'path': path, 'name': path, 'reason': 'workflow_missing_or_disabled',
                             'run_id': None, 'url': ''})
    return findings, healthy, unchecked


def alert(api, findings: list[dict]):
    # One issue per workflow and failure run. Never retries, republishes or changes production workflows.
    issues = []
    for page in range(1, 11):
        batch = api.request(f'/issues?state=all&per_page=100&page={page}').copy()
        issues.extend(i for i in batch if 'pull_request' not in i)
        if len(batch) < 100:
            break
    titles = {issue['title'] for issue in issues}
    posted = 0
    for finding in findings:
        title = f"[OLDIES WATCHDOG] {finding['reason']}: {finding['path']} (run {finding['run_id'] or 'none'})"
        if title in titles:
            continue
        body = (f"Automated GitHub Actions audit; not a confirmation of WordPress/social-media delivery.\n\n"
                f"- Workflow: `{finding['name']}` (`{finding['path']}`)\n"
                f"- Finding: `{finding['reason']}`\n"
                f"- Run: {finding['url'] or 'none'}\n\n"
                "Review the logs before any retry. Do not rerun a publishing workflow without checking for duplicates.")
        api.request('/issues', method='POST', data={'title': title, 'body': body})
        titles.add(title)
        posted += 1
    return posted


def main() -> int:
    cfg_path = Path(__file__).with_name('watchdog-config.json')
    config = json.loads(cfg_path.read_text(encoding='utf-8'))
    api = GitHub(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'],
                 os.environ.get('GITHUB_API_URL', 'https://api.github.com'))
    findings, healthy, unchecked = collect(api, config, datetime.now(timezone.utc))
    rows = [f"## OLDIES WATCHDOG — GitHub Actions\n",
            f"- Healthy/latest run not flagged: {len(healthy)}",
            f"- Requires review: {len(findings)}",
            f"- No runs, freshness rule not configured: {len(unchecked)}",
            "- Scope: GitHub Actions status only; publication delivery is NOT verified.",
            "- No automated retries or live changes.\n"]
    for f in findings:
        rows.append(f"- **{f['reason']}** — `{f['path']}` — {f['url'] or 'no run'}")
    if unchecked:
        rows.append('\nUnchecked (configure expected cadence if scheduled): ' + ', '.join(f'`{p}`' for p in unchecked))
    if config.get('issue_alerts_enabled', False) and findings:
        rows.append(f"\nNew deduplicated GitHub issues: {alert(api, findings)}")
    summary = '\n'.join(rows)
    print(summary)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(summary + '\n')
    # Intentionally do not fail job for observed incidents: preserves the audit report.
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (urllib.error.URLError, ValueError, KeyError) as exc:
        print(f'Watchdog audit error: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)
