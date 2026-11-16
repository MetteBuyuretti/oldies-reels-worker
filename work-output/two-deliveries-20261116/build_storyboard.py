"""Prepare the new English review package; no provider or publishing calls."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1] / 'oldies-reels-repair'
sys.path.insert(0, str(ROOT))
from worker import draw_text_block
from facebook_global_visuals import select_period_photos, full_frame_canvas
from facebook_global_audio import SIGNOFFS, spoken_word_count, TEMPLATE

OUT = Path(__file__).resolve().parent / 'english-with-the-beatles'
OUT.mkdir(exist_ok=True)
VOICE_READY = (OUT / 'dj-story-en.wav').is_file()
STORY = ('Between tours and radio shows, the Beatles made their second album. '
         'With the Beatles reached British shops on November twenty-second, nineteen sixty-three, '
         'mixing Lennon–McCartney originals with favourites from their stage set. '
         'Imagine hearing that record for the very first time.')
c = {'id':'en-with-the-beatles-19631122-review-20261116', 'status':'PREPRODUCTION_VOICE_PENDING',
     'created_at':'2026-11-16T19:10:00Z', 'artist':'The Beatles', 'event_date':'1963-11-22',
     'event_headline':'With The Beatles', 'date_label':'22 November 1963', 'kind':'events',
     'dj_story_text':STORY, 'source_text':STORY, 'signoff_profile':'calm',
     'sources':['https://www.thebeatles.com/beatles',
                'https://www.thebeatles.com/22-november-1963-beatles-released'],
     'facts':[{'claim':'UK second album released 22 November 1963','source_index':0},
              {'claim':'Recorded between touring, radio and TV commitments','source_index':1},
              {'claim':'Lennon–McCartney originals alongside stage-repertoire songs','source_index':0}],
     'copy_note':'Final sentence is an invitation to imagine, not an historical factual claim.',
     'publication_approved':False, 'final_media_approved':False,
     'narration_generated':False, 'measured_duration_seconds':None,
     'target_wpm':128, 'advert_gap_seconds':1.1, 'ending_tail_seconds':0.6,
     'station_ending':dict(SIGNOFFS['calm']),
     'tts_direction':'Warm, natural Charon radio DJ; read the exact story once at about 128 wpm. '
                     'No added words, singing, music, effects or time stretching. Generate the story only; '
                     'reuse the accepted station ending unchanged after 1.1 seconds of silence.'}
photos, selection = select_period_photos(c)
c['image_credits'], c['photo_year_selection'] = photos, selection
words = spoken_word_count(STORY)
c['spoken_words_estimated'] = words
c['estimated_video_seconds'] = round(words / 128 * 60 + 1.1 + 6.72 + .6, 3)
c['duration_note'] = 'Estimate only; final narration and video must be measured and pass 25–30 seconds.'
content = [('WITH THE BEATLES','22 November 1963','A MOMENT IN MUSIC'),
           ('THE SHOWS WENT ON','A second album, made between tours, radio and TV.','THE STORY'),
           ('Timeless music','Listen, enjoy, share.\noldiesradyo.com/en/','OLDIES RADYO • MUSIC & MEMORIES')]
font = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
for i,(p,text) in enumerate(zip(photos,content),1):
    canvas = full_frame_canvas(ROOT/p['asset'])
    d=ImageDraw.Draw(canvas)
    d.text((72,70),'ARCHIVE PHOTOGRAPH • 1963',font=font(24),fill=(236,193,77,255))
    draw_text_block(d,*text)
    if not VOICE_READY:
        d.text((96,1770),'VISUAL PREVIEW • VOICE PENDING',font=font(29),fill=(181,181,181,255))
    canvas.convert('RGB').save(OUT/f'scene-{i}.jpg',quality=94,optimize=True)
sheet=Image.new('RGB',(1620,1100),(10,10,14))
d=ImageDraw.Draw(sheet)
d.text((35,24),'OLDIES RADYO — NEW ENGLISH STORYBOARD',font=font(34),fill=(236,193,77))
d.text((35,75),'16 NOV 2026 • Narrated review copy' if VOICE_READY else '16 NOV 2026 • Visual review only • Narration and measured final film pending',font=font(22),fill='white')
for i in range(1,4):
    with Image.open(OUT/f'scene-{i}.jpg') as im:
        sheet.paste(im.resize((540,960),Image.Resampling.LANCZOS),((i-1)*540,130))
sheet.save(OUT/'storyboard.jpg',quality=93,optimize=True)
(OUT/'candidate.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
(OUT/'story.txt').write_text(STORY+'\n')
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
          for p in OUT.iterdir() if p.is_file()}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'estimated_seconds':c['estimated_video_seconds'],'spoken_words_estimated':words,
                  'photo_years':selection['photo_years'],'files':manifest},indent=2))
