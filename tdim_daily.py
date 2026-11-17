"""Exact-day This Day in Music discovery and binding; no TTS or publishing."""
from datetime import date
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import argparse
import json
import re
from pathlib import Path
import requests

MONTHS = ('', 'january', 'february', 'march', 'april', 'may', 'june',
          'july', 'august', 'september', 'october', 'november', 'december')


def source_url(day):
    d = date.fromisoformat(day)
    return f'https://www.thisdayinmusic.com/on-this-day-in-music-{MONTHS[d.month]}-{d.day}/'


def plain(text):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]*>', ' ', text))).strip()


def fingerprint(text):
    return sha256(plain(text).encode()).hexdigest()


class Entries(HTMLParser):
    def __init__(self):
        super().__init__(); self.items = []

    def handle_comment(self, text):
        # TDIM embeds the same database record beside each visible event row.
        match = re.fullmatch(r'\s*<pre>\s*(\{.*\})\s*</pre>\s*', text, re.S)
        if match:
            try: self.items.append(json.loads(match[1]))
            except (ValueError, TypeError): pass


def parse_events(html, day):
    d = date.fromisoformat(day); parser = Entries(); parser.feed(html)
    items = []; seen = set()
    for raw in parser.items:
        try:
            year = int(raw['nYear'])
            if (int(raw['nDay']), int(raw['nMonth'])) != (d.day, d.month): continue
            if str(raw['nEventID']) != '1' or not 1950 <= year <= 1999: continue
            event_date = date(year, d.month, d.day).isoformat()
        except (KeyError, TypeError, ValueError): continue
        ident = str(raw.get('nID', '')); text = plain(raw.get('sDescription', ''))
        if not ident.isdigit() or ident in seen or len(text) < 30: continue
        seen.add(ident)
        items.append({'source_event_id': ident, 'event_date': event_date,
                      'artist': plain(raw.get('sArtist', '')), 'source_text': text,
                      'source_url': source_url(day), 'source_sha256': fingerprint(text)})
    if not items:
        raise RuntimeError('This Day in Music exact-day event parser returned no 1950s-1990s entries; no archive substitution')
    return items


def fetch_events(day, output=None, session=requests):
    url = source_url(day)
    response = session.get(url, headers={'User-Agent': 'OldiesRadyoBot/1.0 (https://oldiesradyo.com)',
                                       'Accept': 'text/html'}, timeout=35)
    response.raise_for_status()
    if response.url.rstrip('/') != url.rstrip('/'):
        raise RuntimeError('This Day in Music redirected to a different day or source')
    if len(response.content) > 3 * 1024 * 1024:
        raise RuntimeError('This Day in Music response exceeds expected size')
    events = parse_events(response.text, day)
    if output:
        output = Path(output); output.mkdir(parents=True, exist_ok=True)
        (output / 'daily-source.json').write_text(json.dumps(
            {'production_day': day, 'source_url': url, 'events': events}, indent=2))
    return events


def matches(candidate, entry, day):
    binding = candidate.get('daily_source') or {}
    canonical = lambda s: re.sub(r'^the\s+', '', plain(s).casefold())
    return (candidate.get('reviewed') is True and candidate.get('event_date') == entry['event_date']
            and canonical(candidate.get('artist', '')) == canonical(entry['artist'])
            and candidate['event_date'][5:] == day[5:]
            and binding.get('provider') == 'thisdayinmusic.com'
            and str(binding.get('event_id')) == entry['source_event_id']
            and binding.get('source_url') == entry['source_url']
            and binding.get('source_sha256') == entry['source_sha256']
            and entry['source_url'] in candidate.get('sources', []))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--day', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(json.dumps(fetch_events(args.day, args.output), indent=2))
