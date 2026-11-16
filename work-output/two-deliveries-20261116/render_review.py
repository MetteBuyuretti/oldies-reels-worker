"""Assemble the actual downloaded free Charon take; no API or publication calls."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / 'oldies-reels-repair'
sys.path.insert(0,str(ROOT))
import facebook_global_audio as a
import facebook_global_visuals as v

out = HERE / 'english-with-the-beatles'
c = json.loads((out/'candidate.json').read_text())
source = out/'dj-story-en.wav'
assert hashlib.sha256(source.read_bytes()).hexdigest() == 'ed960e671cf2d1be7ff69023e4acacbde7976a813586ce2da1cb3835c3518f93'
story = a.inspect_audio(source)
story.pop('streams')
words = a.spoken_word_count(c['dj_story_text'])
wpm = words * 60 / story['duration_seconds']
assert wpm <= a.TEMPLATE['max_estimated_wpm']
profile, identity, ending_bytes = a.selected_signoff(c)
ending = out/'dj-advert-en.mp3'
ending.write_bytes(ending_bytes)
ending_qc=a.inspect_audio(ending)
assert abs(ending_qc['duration_seconds']-identity['duration_seconds']) < .05
voice = out/'voiceover-facebook-en.mp3'
graph=('[0:a]aresample=48000,aformat=channel_layouts=mono[a];'
       'anullsrc=r=48000:cl=mono,atrim=duration=1.1,asetpts=PTS-STARTPTS[gap];'
       '[1:a]aresample=48000,aformat=channel_layouts=mono[b];'
       '[a][gap][b]concat=n=3:v=0:a=1[voice]')
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(source),'-i',str(ending),
                '-filter_complex',graph,'-map','[voice]','-c:a','libmp3lame','-b:a','192k',str(voice)],check=True)
combined=a.inspect_audio(voice)
c.update(status='NARRATED_REVIEW_PENDING_LISTENING',narration_generated=True,
         narration_model='gemini-2.5-flash-preview-tts',narration_voice='Charon',
         source_wav_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
         narration_provenance='Google AI Studio UI; no API key selected; free model; exact downloaded WAV',
         tts_language='en-US',tts_voice='Charon',tts_engine='gemini-2.5-flash-preview-tts-aistudio',
         voiceover={'enabled':True,'source':'google_ai_studio_free_flash_download'},
         dj_script_en=c['dj_story_text']+' '+a.BRAND_ADVERT,
         voiceover_duration_seconds=combined['duration_seconds'])
c['dj_recording']={'version':a.TEMPLATE['version'],'brand_name':a.BRAND_NAME,
    'story_text':c['dj_story_text'],'advert_text':a.BRAND_ADVERT,
    'story':{'duration_seconds':story['duration_seconds'],'spoken_words_estimated':words,
             'estimated_wpm':round(wpm,1),'tempo_factor':1.0},
    'advert':{'duration_seconds':ending_qc['duration_seconds'],'cached_approved_recording':True},
    'advert_gap_seconds':1.1,'advert_start_seconds':round(story['duration_seconds']+1.1,3),
    'speedup_applied':False,'background_music_added':False,
    'advert_sha256':identity['sha256'],'signoff_profile':profile,
    'signoff_evidence':a.SIGNOFF_EVIDENCE,'signoff_source':identity['asset'],
    'signoff_approval':'accepted-station-ending-only','final_media_approved':False}
c['visual_qc']={'template':'existing-gold-white-three-scene','photography':'reviewed-period-originals',
               'full_source_frame_visible':True,'crop_applied':False,'zoom_applied':False,
               'distinct_photos':3,'photo_region':[56,120,1024,890],'version':a.TEMPLATE['version']}
video=out/'OldiesRadyo-WithTheBeatles-EN-Review-20261116.mp4'
v.render([out/f'scene-{i}.jpg' for i in range(1,4)],video,voice,c,100*1024*1024)
c['audio_qc']=a.validate_media(video,c)
c['audio_qc'].update(a.validate_recording(video,c))
c['audio_qc'].pop('streams',None)
c['measured_duration_seconds']=c['audio_qc']['video_duration_seconds']
c['video_sha256']=hashlib.sha256(video.read_bytes()).hexdigest()
c['video_bytes']=video.stat().st_size
c['publication_approved']=False
c['final_media_approved']=False
c['human_listening_verified']=False
c['independent_watchdog_acceptance']=False
c['automation_model_note']='This free UI take does not change the quarantined automation default Pro model or enable a schedule.'
(out/'candidate.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
(out/'dj-recording.json').write_text(json.dumps(c['dj_recording'],ensure_ascii=False,indent=2)+'\n')
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
          for p in out.iterdir() if p.is_file() and p.name!='manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'video':str(video),'duration':c['measured_duration_seconds'],'qc':c['audio_qc'],
                  'bytes':c['video_bytes'],'sha256':c['video_sha256']},indent=2))
