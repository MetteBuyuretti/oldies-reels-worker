"""Original, sourced OLDIES editorial stock. No publication or paid API calls."""
import json, html, os, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(os.environ.get('OLDIES_EDITORIAL_OUT',str(Path(__file__).parent/'editorial-stock')))
ROOT.mkdir(parents=True,exist_ok=True)
S=[
('elvis-suspicious-minds-1969','When a Familiar Voice Finds a New Room','ELVIS / 1969','SUSPICIOUS\nMINDS','vinyl',[
'Elvis Presley recorded “Suspicious Minds” at American Sound Studio in Memphis in January 1969. The song was written by Mark James; the official session credits name a roomful of musicians behind the voice. A familiar singer, a different setting, and a record worth hearing with fresh ears.',
'Try following the bass and drums before concentrating on Elvis. Then notice how his voice moves from a quiet invitation towards something much more urgent. The pleasure is in that growing conversation between a singer and the people playing around him.',
'Graceland’s chronology places the single among the successes that followed those Memphis sessions. You do not need the chart history to enjoy the tension in the performance, but it is a reminder that a long career can still contain a new beginning.',
'Which record made you hear a favourite singer differently? Put it beside “Suspicious Minds” and listen again with OLDIES RADYO.'
], [('Elvis Presley official session credits','https://www.elvisthemusic.com/track/suspicious-minds/'),('Graceland: 1966–1969 chronology','https://www.graceland.com/1966---1969')]),
('george-michael-faith-1987','The Space Between the Beats on Faith','GEORGE MICHAEL / 1987','FIND THE\nGROOVE','guitar',[
'George Michael’s official catalogue dates Faith to October 30, 1987. The Rock & Roll Hall of Fame describes an artist whose sense of melody travelled through rock, R&B and electronic music. Returning to the album is a chance to hear those interests sharing the same space.',
'Start with the title track and listen for what is left open. The guitar gives the rhythm its shape, while the vocal can lean into a phrase and pull away again. A recording does not need to fill every corner to hold your attention.',
'Then move to a slower song and notice how the mood changes without losing the singer’s personality. That contrast makes an album more than a row of familiar singles; it becomes somewhere you can spend a little time.',
'Which track do you return to after the big hit has finished? Bring that favourite back into your listening day with OLDIES RADYO.'
], [('George Michael official catalogue','https://store.georgemichael.com/products/faith-cd'),('Rock & Roll Hall of Fame: George Michael','https://rockhall.com/inductees/george-michael/')]),
('aretha-respect-1967','A Voice That Makes Every Word Count','ARETHA FRANKLIN / 1967','LISTEN TO\nTHE VOICE','mic',[
'Aretha Franklin’s 1967 recording of “Respect” brought a new voice and perspective to a song written by Otis Redding. The Recording Academy records its success, and the Library of Congress places it among the remarkable run of singles she released that year.',
'Listen past the familiarity of the title. Hear how the lead vocal and the answering voices push the rhythm forward. There is firmness in the delivery, but also playfulness in the exchanges; the record feels alive because the parts keep responding to one another.',
'An old favourite can become background music if we let it. Give this one a few uninterrupted minutes instead. Which tiny vocal turn catches your ear when you stop waiting for the part you already know?',
'Tell us which soul record always makes you turn the radio up. There are more voices to rediscover at OLDIES RADYO.'
], [('Library of Congress: Aretha Franklin and Respect','https://blogs.loc.gov/loc/2018/08/aretha-franklin-and-respect/'),('Recording Academy: Aretha Franklin','https://www.grammy.com/artists/aretha-franklin/11503/')]),
('beatles-rubber-soul-1965','A Small Detour Through Rubber Soul','THE BEATLES / 1965','ANOTHER\nWAY TO LISTEN','guitar',[
'The Beatles released the UK edition of Rubber Soul on December 3, 1965. Their official album history points to the sitar on “Norwegian Wood” as one sign of their growing curiosity about new sounds. Official Charts records the album’s arrival in the British chart that month.',
'You can listen for that curiosity without turning the record into a lesson. Follow an unfamiliar texture, a change in the harmonies, or a guitar part you had previously overlooked. The songs are familiar enough to welcome you in, but detailed enough to reward a detour.',
'The British and American editions did not have identical track lists, so a favourite running order may depend on the copy you grew up with. That little difference is part of the story of living with records, too.',
'Which album do you still hear in its original order? Take a favourite side for another spin with OLDIES RADYO.'
], [('The Beatles: Rubber Soul album history','https://www.thebeatles.com/rubber-soul'),('Official Charts: Rubber Soul','https://www.officialcharts.com/albums/the-beatles-rubber-soul/')]),
('walkman-listening-1979','When the Walk Became Part of the Music','LISTENING CULTURE / 1979','YOUR WALK.\nYOUR SOUNDTRACK.','cassette',[
'Sony introduced its first Walkman, the TPS-L2, in 1979. Its anniversary history describes the pairing of a small cassette player with lightweight headphones; museum collections preserve the blue-and-silver device as an object from a changing listening culture.',
'Think of the small ritual rather than the specifications: choosing a tape, checking the batteries, deciding which side would accompany the journey. A familiar street could take on a different mood when the music belonged only to you.',
'A cassette also asked for a little patience. There was a side to finish and sometimes a favourite passage to rewind. That limitation could make an ordinary trip feel like time set aside for an album.',
'Which cassette would you choose for a long walk today? Keep that private soundtrack feeling alive with OLDIES RADYO.'
], [('Sony: Walkman twentieth-anniversary history','https://www.sony.com/en/SonyInfo/News/Press/199907/99-059/'),('Museum collection: Sony TPS-L2','https://onlinesammlung.museumsstiftung.de/detail/collection/612bb3cf-a5bf-4793-b75c-27c619fbbf79')]),
('abba-waterloo-1974','Before the Chorus Becomes a Memory','ABBA / 1974','BACK TO\nWATERLOO','mic',[
'On April 6, 1974, ABBA won the Eurovision Song Contest in Brighton with “Waterloo”. Both the group’s own history and the contest’s archive preserve that meeting of a Swedish pop group, a bright stage and a song ready to travel.',
'Listen to the recording without picturing the costumes for a moment. The voices and the beat keep handing the song forward; each return to the chorus feels like an invitation to join in. The performance is full of carefully arranged details, even when its energy seems effortless.',
'A competition result can give a record a date in the history books. What keeps it in everyday life is simpler: someone still wants to sing it in a kitchen, on a car journey, or with friends at the end of an evening.',
'Which ABBA song belongs to a particular place in your memory? Find another reason to sing along at OLDIES RADYO.'
], [('ABBA: the official story','https://abbasite.com/story/'),('Eurovision: Brighton 1974 archive','https://www.eurovision.com/eurovision-song-contest/brighton-1974/')]),
('dolly-jolene-album-1974','The Quiet Tension Inside Jolene','DOLLY PARTON / 1974','A STORY\nIN A VOICE','guitar',[
'Dolly Parton’s Jolene album arrived in February 1974, following the title song’s release as a single in 1973. Her official album notes place “Jolene” beside “I Will Always Love You”: two songs that approach difficult feelings from very different directions.',
'Start with the title track’s repeating guitar figure. The movement is steady, while the voice carries the uncertainty. You can hear how a small musical idea gives a story somewhere to unfold without crowding it.',
'Then listen to the space around the singing. A direct performance can draw you closer than a dramatic arrangement; you start paying attention to breath, emphasis and the change of feeling inside an ordinary word.',
'Which storyteller can hold your attention with just a voice and a guitar? Make room for another close listen with OLDIES RADYO.'
], [('Dolly Parton: official Jolene album notes','https://www.dollyparton.com/album/jolene'),('HISTORY: the Jolene single','https://www.history.com/this-day-in-history/October-15/dolly-parton-jolene-single-released')]),
('donna-summer-feel-love-1977','A Human Voice Inside an Electronic Pulse','DONNA SUMMER / 1977','FEEL THE\nPULSE','synth',[
'Donna Summer’s “I Feel Love” reached the UK singles chart in 1977. The GRAMMY Museum’s Hall of Fame notes describe its recording with Giorgio Moroder and Pete Bellotte and the electronic pulse that helped make the song sound so distinctive.',
'Listen to the repeating synthesizer pattern, then let your attention move to Summer’s voice. One seems built to keep going; the other floats, stretches and changes the temperature of the music. The fascination is in hearing those two kinds of movement together.',
'You do not need to be on a dance floor to enjoy that balance. Through headphones, a familiar club record can reveal little shifts in texture that disappear when you hear it only as a burst of energy.',
'Which dance record still sounds fresh when the room is quiet? Follow the pulse a little further with OLDIES RADYO.'
], [('Official Charts: I Feel Love','https://www.officialcharts.com/songs/donna-summer-i-feel-love/'),('GRAMMY Museum: 2024 Hall of Fame notes','https://grammymuseum.org/wp-content/uploads/2024/07/24_HOF_ProgramBook2-5.pdf')]),
('supremes-baby-love-1964','The Little Details That Keep Baby Love Moving','THE SUPREMES / 1964','A LITTLE\nMOTOWN MAGIC','vinyl',[
'“Baby Love” was one of the Supremes’ great successes of 1964. The Motown Museum traces the group’s rise through that extraordinary run of records, while Detroit’s own historical society places the song among their defining hits.',
'Try listening once for the answering vocals rather than the lead. Then return to the rhythm beneath them. The charm comes from the way all those small parts move together, giving a short pop record its sense of forward motion.',
'Nostalgia can make a song seem as though it has always existed. Close listening brings back the work inside it: people choosing how to phrase a line, where to leave room, and when to step forward.',
'Which Motown record always finds its way into your day? There is room for another favourite at OLDIES RADYO.'
], [('Motown Museum: the Supremes','https://www.motownmuseum.org/artist/supremes/'),('Detroit Historical Society: the Supremes','https://www.detroithistorical.org/learn/online-research/encyclopedia-of-detroit/supremes')]),
]

def font(n,bold=False):
    candidates=[Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf'),Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    return ImageFont.truetype(str(next(p for p in candidates if p.exists())),n)

def art(p,index):
    palettes=[('#171c27','#f7e9cf','#dca45d','#bc5042'),('#223b42','#f3ebd6','#eda75b','#b9554a'),('#4d2035','#fff0d5','#ddad57','#79a5a0')]
    bg,cream,gold,accent=palettes[index%3]; im=Image.new('RGB',(1200,1500),bg);d=ImageDraw.Draw(im)
    d.rectangle((45,45,1155,1455),outline=gold,width=2)
    d.text((95,92),'OLDIES RADYO',font=font(34,True),fill=gold)
    d.line((95,155,1105,155),fill=gold,width=2)
    d.text((95,205),p['kicker'],font=font(31),fill=cream)
    y=280
    for line in p['headline'].split('\n'):
        size=92
        while d.textlength(line,font=font(size,True))>1010:size-=2
        d.text((90,y),line,font=font(size,True),fill=cream);y+=115
    cx,cy=600,900
    if p['motif']=='vinyl':
        d.ellipse((270,570,930,1230),fill='#101014',outline=gold,width=5)
        for r in range(130,325,16):d.ellipse((cx-r,cy-r,cx+r,cy+r),outline='#55504c',width=2)
        d.ellipse((495,795,705,1005),fill=accent);d.ellipse((583,883,617,917),fill=cream)
        d.line((995,660,1020,1000,855,1090),fill=gold,width=17)
    elif p['motif']=='guitar':
        d.ellipse((350,875,780,1250),fill=accent,outline=gold,width=6)
        d.ellipse((420,760,735,1090),fill=accent,outline=gold,width=6)
        d.rounded_rectangle((540,560,625,1020),radius=10,fill=gold)
        d.ellipse((505,940,660,1095),fill=bg,outline=cream,width=5)
        for off in range(0,65,12):d.line((550+off,585,550+off,1170),fill=cream,width=2)
        for yy in range(630,900,40):d.line((540,yy,625,yy),fill=bg,width=2)
        d.rectangle((500,1155,665,1180),fill=bg)
    elif p['motif']=='cassette':
        d.rounded_rectangle((220,680,980,1160),radius=40,fill=accent,outline=gold,width=7)
        d.rounded_rectangle((275,740,925,1005),radius=20,fill=cream)
        for xx in (415,785):
            d.ellipse((xx-100,775,xx+100,975),fill=bg);d.ellipse((xx-42,833,xx+42,917),outline=gold,width=10)
        d.line((415,775,785,775),fill=bg,width=7);d.line((415,975,785,975),fill=bg,width=7)
        d.polygon([(390,1080),(810,1080),(855,1145),(345,1145)],fill=bg)
    elif p['motif']=='mic':
        d.rounded_rectangle((450,600,750,1010),radius=140,fill=cream)
        for yy in range(660,975,38):d.line((485,yy,715,yy),fill=bg,width=13)
        d.arc((380,800,820,1120),0,180,fill=gold,width=16)
        d.line((600,1120,600,1250),fill=gold,width=18);d.line((450,1250,750,1250),fill=gold,width=18)
    else:
        for i,h in enumerate([120,220,320,260,180,350,270,140,210]):
            xx=200+i*90;d.rounded_rectangle((xx,1050-h,xx+45,1100),radius=20,fill=accent if i%2 else gold)
        d.line((180,1150,1020,1150),fill=cream,width=4)
        for i in range(12):d.rectangle((205+i*65,1180,260+i*65,1250),fill=cream)
    d.text((95,1330),'MUSIC. MEMORIES. A CLOSER LISTEN.',font=font(25,True),fill=gold)
    d.text((95,1390),'Original editorial illustration • oldiesradyo.com',font=font(21),fill=cream)
    image=ROOT/p['image'];im.save(image,optimize=True)

posts=[]
for i,(id,title,kicker,headline,motif,pars,sources) in enumerate(S):
    utm=f'https://oldiesradyo.com/?utm_source=tumblr&utm_medium=social&utm_campaign=music_stories_202611&utm_content={id}'
    p=dict(id=id,title=title,kicker=kicker,headline=headline,motif=motif,paragraphs=pars,sources=[dict(label=l,url=u) for l,u in sources],tags=[kicker.split(' / ')[0].lower(),'music history','oldies radio','close listening'],alt=f'Original OLDIES RADYO editorial illustration: a stylised {motif}, with the words {headline.replace(chr(10)," ")} and {kicker}. Conceptual artwork; no artist photograph or album cover is reproduced.',utm=utm,image=id+'.png',language='en',publicationApproval=False,status='READY_FOR_DRAFT',created='2026-11-05',cost=0,rights=dict(type='original programmatic editorial illustration',creator='OLDIES RADYO, created for the 5 November 2026 repair',thirdPartyAssets=False,archivalPhoto=False,aiGeneratedRaster=False),targetAt=f'2026-11-{5+i//3:02d}T{[10,16,22][i%3]:02d}:00:00+03:00')
    p['bodyHtml']=''.join('<p>'+html.escape(x)+'</p>' for x in pars)+'<p>Sources: '+' · '.join(f'<a href="{html.escape(u,quote=True)}">{html.escape(l)}</a>' for l,u in sources)+'</p><p>Original editorial illustration for OLDIES RADYO; not an archival photograph.</p><p>Discover more at OLDIES RADYO: <a href="'+html.escape(utm,quote=True)+'">https://oldiesradyo.com/</a></p>'
    art(p,i);posts.append(p)
(ROOT/'new-editorial-posts.json').write_text(json.dumps(dict(schemaVersion=1,blog='oldiesradyo',publishMode='REVIEWED_DRAFTS',posts=posts),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'created':len(posts),'images':[(p['id'],(ROOT/p['image']).stat().st_size) for p in posts],'publicationCalls':0}))
