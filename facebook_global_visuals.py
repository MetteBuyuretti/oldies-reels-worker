"""Reviewed, full-frame period photography for Facebook Global English only."""
from __future__ import annotations
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from facebook_global_audio import TEMPLATE, inspect_audio

ROOT = Path(__file__).resolve().parent
BANNED = re.compile(r'\b(?:statue|plaque|memorial|ticket|logo|building|cropped|crop|collage|illustration)\b', re.I)
REVIEW_FLAGS = ('approved', 'artist_verified', 'period_verified', 'complete_composition', 'quality_reviewed', 'artist_dominant')


def validate_photo(photo: dict, artist: str, event_year: int, root: Path = ROOT) -> Path:
    if any(photo.get(flag) is not True for flag in REVIEW_FLAGS):
        raise RuntimeError('Photo rejected: editorial approval and subject/period/full-frame review required')
    if str(photo.get('artist', '')).casefold() != artist.casefold():
        raise RuntimeError('Photo rejected: wrong artist')
    if BANNED.search(str(photo.get('title', ''))) or photo.get('derived_variant') or photo.get('source_cropped'):
        raise RuntimeError('Photo rejected: non-photo subject, crop or derived duplicate')
    distance = abs(int(photo.get('photo_year', 0)) - event_year)
    if distance > TEMPLATE['maximum_period_distance_years']:
        raise RuntimeError('Photo rejected: outside the locked event-year policy')
    if distance > TEMPLATE['automatic_period_distance_years']:
        if distance != TEMPLATE['manual_period_distance_years'] or photo.get('manual_period_override') is not True or not str(photo.get('manual_period_note', '')).strip():
            raise RuntimeError('Photo rejected: ±2-year use requires explicit manual period approval')
    if not photo.get('date_evidence') or not str(photo.get('source', '')).startswith('https://commons.wikimedia.org/wiki/File:'):
        raise RuntimeError('Photo rejected: missing source or date evidence')
    license_name = str(photo.get('license', '')).casefold()
    if not any(marker in license_name for marker in ('public domain', 'cc0', 'cc by')) or any(marker in license_name for marker in ('nc', 'nd')):
        raise RuntimeError('Photo rejected: approved reuse license required')
    path = (root / str(photo.get('asset', ''))).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise RuntimeError('Photo rejected: approved asset missing')
    if hashlib.sha256(path.read_bytes()).hexdigest() != photo.get('sha256'):
        raise RuntimeError('Photo rejected: approved asset changed since review')
    with Image.open(path) as image:
        if max(image.size) < 1080:
            raise RuntimeError('Photo rejected: insufficient resolution')
        image.verify()
    return path


def load_period_photos(candidate: dict, directory: Path, root: Path = ROOT) -> tuple[list[Path], list[dict]]:
    bank = json.loads((root / TEMPLATE['photo_bank']).read_text(encoding='utf-8'))
    artist, year = str(candidate['artist']), int(str(candidate['event_date'])[:4])
    photos, credits, seen = [], [], set()
    entries = [entry for entry in bank['photos'] if str(entry.get('artist', '')).casefold() == artist.casefold()]
    # Immutable selection order: same event year first, then ±1; ±2 only when manually approved.
    entries.sort(key=lambda entry: (abs(int(entry.get('photo_year', 0)) - year), int(entry.get('photo_year', 0))))
    for entry in entries:
        try:
            source = validate_photo(entry, artist, year, root)
        except RuntimeError as exc:
            print(exc)
            continue
        key = entry.get('composition_id')
        if not key or key in seen or entry['sha256'] in seen:
            continue
        path = directory / f'photo-{len(photos) + 1}.jpg'
        shutil.copyfile(source, path)
        photos.append(path); credits.append(dict(entry)); seen.update((key, entry['sha256']))
        if len(photos) == TEMPLATE['photo_count']:
            break
    if len(photos) != TEMPLATE['photo_count']:
        raise RuntimeError(f'Facebook photo gate: {artist} requires three distinct reviewed full-frame period photographs; found {len(photos)}')
    return photos, credits


def full_frame_canvas(photo: Path, width: int = 1080, height: int = 1920) -> Image.Image:
    canvas = Image.new('RGBA', (width, height), (10, 10, 14, 255))
    # Contain the complete source; no side crops, zoom, blur-fill or overlaid text.
    with Image.open(photo) as opened:
        image = ImageOps.exif_transpose(opened).convert('RGB')
        contained = ImageOps.contain(image, (width - 112, 770), Image.Resampling.LANCZOS)
    x, y = (width - contained.width) // 2, 120 + (770 - contained.height) // 2
    canvas.paste(contained, (x, y))
    return canvas


def make_scenes(candidate: dict, photos: list[Path], directory: Path, draw_text_block) -> list[Path]:
    if len(photos) != 3:
        raise RuntimeError('Facebook template requires three approved photographs')
    story, advert = candidate['dj_recording']['story_text'], candidate['dj_recording']['advert_text']
    content = [(str(candidate.get('event_headline') or candidate['artist']), str(candidate['date_label']), 'ON THIS DAY IN MUSIC'),
               (str(candidate['artist']), story.split(' — on this day')[0], 'THE STORY'),
               ('Timeless music', 'Listen, enjoy, share.\noldiesradyo.com/en/', 'OLDIES RADYO • MUSIC & MEMORIES')]
    paths = []
    for index, (photo, text) in enumerate(zip(photos, content), 1):
        canvas = full_frame_canvas(photo)
        draw = ImageDraw.Draw(canvas)
        from PIL import ImageFont
        archive_year = candidate["image_credits"][index - 1]["photo_year"]
        draw.text((72, 70), f"ARCHIVE PHOTOGRAPH • {archive_year}",
                  font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24), fill=(236, 193, 77, 255))
        draw_text_block(draw, *text)
        path = directory / f'scene-{index}.jpg'
        canvas.convert('RGB').save(path, 'JPEG', quality=95, optimize=True)
        paths.append(path)
    candidate['visual_qc'] = {'template': 'existing-gold-white-three-scene', 'photography': 'reviewed-period-originals',
                              'full_source_frame_visible': True, 'crop_applied': False, 'zoom_applied': False,
                              'distinct_photos': 3, 'photo_region': [56, 120, 1024, 890], 'version': TEMPLATE['version']}
    return paths


def render(scenes: list[Path], target: Path, voiceover: Path, candidate: dict, max_video_bytes: int) -> None:
    qc = inspect_audio(voiceover)
    duration = max(15, math.ceil(qc['duration_seconds'] + TEMPLATE['ending_tail_seconds']))
    if duration > TEMPLATE['max_video_seconds']:
        raise RuntimeError('Facebook relaxed recording cannot fit; shorten copy instead of accelerating')
    fade = 0.35
    first = max(3.0, candidate['dj_recording']['story']['duration_seconds'] / 2)
    second = candidate['dj_recording']['advert_start_seconds'] - fade
    if second <= first + fade or second >= duration - 1:
        raise RuntimeError('Facebook story and station promotion timing is invalid')
    lengths = (first + fade, second - first + fade, duration - second)
    inputs, graph = [], []
    for index, (scene, length) in enumerate(zip(scenes, lengths)):
        inputs += ['-loop', '1', '-framerate', '30', '-t', f'{length:.3f}', '-i', str(scene)]
        graph.append(f'[{index}:v]setsar=1,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v{index}]')
    graph += [f'[v0][v1]xfade=transition=fade:duration={fade}:offset={first:.3f}[x]',
              f'[x][v2]xfade=transition=fade:duration={fade}:offset={second:.3f}[v]',
              '[3:a]aformat=sample_rates=48000:channel_layouts=stereo,highpass=f=70,lowpass=f=16000,loudnorm=I=-16:TP=-1.0:LRA=7,apad[voice]']
    command = ['ffmpeg', '-y', '-filter_complex_threads', '1', *inputs, '-i', str(voiceover), '-filter_complex', ';'.join(graph),
               '-map', '[v]', '-map', '[voice]', '-t', str(duration), '-r', '30', '-c:v', 'libx264', '-preset', 'medium',
               '-crf', '24', '-maxrate', '2200k', '-bufsize', '4400k', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
               '-ar', '48000', '-ac', '2', '-movflags', '+faststart', str(target)]
    subprocess.run(command, check=True)
    if not target.is_file() or not 0 < target.stat().st_size <= max_video_bytes:
        raise RuntimeError('Facebook rendered MP4 failed size validation')


def validate_publish(candidate: dict) -> None:
    artist, year = str(candidate.get('artist', '')), int(str(candidate.get('event_date', '0'))[:4])
    credits = candidate.get('image_credits', [])
    if len(credits) != 3 or len({p.get('composition_id') for p in credits}) != 3 or len({p.get('sha256') for p in credits}) != 3:
        raise RuntimeError('Facebook publish blocked: three distinct approved period photos required')
    for photo in credits:
        validate_photo(photo, artist, year)
    visual = candidate.get('visual_qc', {})
    if visual.get('full_source_frame_visible') is not True or visual.get('crop_applied') is not False or visual.get('zoom_applied') is not False:
        raise RuntimeError('Facebook publish blocked: full-frame, no-crop/no-zoom evidence required')
