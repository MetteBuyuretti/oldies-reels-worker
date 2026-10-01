#!/usr/bin/env python3
"""Read the delivery release and report retention decisions. No deletion API."""
import json
import os
import urllib.error
import urllib.request

from retention_policy import retention_decision


def main():
    repo = os.environ['REPOSITORY']
    headers = {'Accept': 'application/vnd.github+json',
               'X-GitHub-Api-Version': '2022-11-28',
               'User-Agent': 'oldies-reels-retention-audit'}

    def read(url):
        request = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError('GitHub inventory HTTP ' + str(exc.code)) from None
        except (urllib.error.URLError, TimeoutError):
            raise RuntimeError('GitHub inventory read failed; no remote writes attempted') from None

    release = read(f'https://api.github.com/repos/{repo}/releases/tags/reels-delivery')
    if not release:
        print('No delivery release; nothing to inventory.')
        return
    if not isinstance(release, dict) or not release.get('id'):
        raise RuntimeError('GitHub inventory invalid release metadata')
    page, count = 1, 0
    while True:
        assets = read(f'https://api.github.com/repos/{repo}/releases/{release["id"]}/assets?per_page=100&page={page}') or []
        if not isinstance(assets, list) or any(not isinstance(asset, dict) for asset in assets):
            raise RuntimeError('GitHub inventory invalid asset metadata')
        for asset in assets:
            if str(asset.get('name', '')).lower().endswith('.mp4'):
                # No trusted WP acknowledgement means preserve recovery data.
                decision = retention_decision(asset)
                print(json.dumps({'asset_id': asset.get('id'), 'name': asset.get('name'), **decision}, ensure_ascii=False))
                count += 1
        if len(assets) < 100:
            break
        page += 1
    print(f'Retention inventory complete: {count} MP4s inspected; zero writes/deletes.')


if __name__ == '__main__':
    main()
